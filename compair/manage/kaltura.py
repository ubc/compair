"""
Migrate Kaltura media to new Kaltura instance. We're switching from on-prem
hosted Kaltura to cloud Kaltura. When videos are transferred to the new Kaltura
instance, a new entry ID is generated. We will be given a CSV mapping of old
to new entry IDs, and will have to update our Kaltura data accordingly.

Assuming that collision between old and new entry IDs are impossible.

Requires that these Kaltura env vars are set to the new Kaltura environment:

* KALTURA_SERVICE_URL
* KALTURA_PARTNER_ID
* KALTURA_SECRET
* KALTURA_USER_ID
* KALTURA_PLAYER_ID

Usage options, run in app root:

    python manage.py kaltura migrate /path/to/mappingCsv.csv

-d Do a dry run, without actually making any changes to the database:

    python manage.py kaltura migrate -d /path/to/mappingCsv.csv

-n If present, tells the CSV parser not to skip the first row. By default, we
assume the first row is a header row and skip it:

    python manage.py kaltura migrate -n /path/to/mappingCsv.csv

"""

import csv
from datetime import datetime
import re
from urllib.parse import unquote_plus

from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Core import (KalturaSessionType, KalturaMediaEntry,
                                        KalturaMediaType)
from flask_script import Manager

from compair.core import db
from compair.kaltura.core import KalturaCore
from compair.models import Answer, KalturaMedia, File
from flask import current_app

manager = Manager(usage="Kaltura Migration")

def readMappingCsv(mappingCsv, noHeader):
    oldToNewEntryIds = {}
    idRe = re.compile(r"\d_\w{8}")
    with open(mappingCsv, 'r') as csvFile:
        csvReader = csv.reader(csvFile, skipinitialspace=True)
        for row in csvReader:
            if not noHeader and csvReader.line_num == 1:
                continue
            oldEntryId = row[0]
            newEntryId = row[1]
            if not (re.match(idRe, oldEntryId) and re.match(idRe, newEntryId)):
                raise ValueError(f"Mapping file line {csvReader.line_num} has a value not in entry ID format.")
            oldToNewEntryIds[oldEntryId] = newEntryId
    if oldToNewEntryIds:
        return oldToNewEntryIds
    raise ValueError("Mapping file is empty")


def msg(msg, logfile):
    print(msg)
    logfile.write(f'{msg}\n')
    logfile.flush()


def summarize(numToMigrate, numInvalid, numMigrated, numNoMapping, numTotal,
              logfile):
    msg( '-------- Summary --------', logfile)
    msg(f'  To be Migrated: {numToMigrate}', logfile)
    msg(f'   To be Deleted: {numInvalid}', logfile)
    msg(f'Already Migrated: {numMigrated}', logfile)
    msg(f'      No Mapping: {numNoMapping}', logfile)
    msg(f'           Total: {numTotal}', logfile)
    msg( '-------- ------- --------', logfile)


def deleteInvalidKalturaMedias(medias, logfile):
    for media in medias:
        msg(f'Deleting invalid kaltura media id {media.id}', logfile)
        db.session.delete(media)


def connectKalturaApi():
    kClient = KalturaClient(KalturaConfiguration(
                            serviceUrl=KalturaCore.service_url()))
    kSession = kClient.session.start(
        KalturaCore.secret(),
        KalturaCore.user_id(),
        KalturaSessionType.ADMIN,
        KalturaCore.partner_id(),
        86400, # session expires in 1 hour
        "appID:compair"
    )
    kClient.setKs(kSession)
    return kClient


def migrateKalturaMedias(medias, oldToNewEntryIds, logfile):
    kClient = connectKalturaApi()

    for media in medias:
        mediaId = media.id
        oldEntryId = media.entry_id
        newEntryId = oldToNewEntryIds[oldEntryId]
        msg(f'Processing id {mediaId}: Old {oldEntryId} to New {newEntryId}',
            logfile)
        newInfo = kClient.media.get(newEntryId, -1)
        media.download_url = newInfo.getDownloadUrl()
        media.partner_id = newInfo.getPartnerId()
        media.service_url = KalturaCore.service_url()
        media.player_id = KalturaCore.player_id()
        media.entry_id = newEntryId
        #db.session.add(media)


# Some videos were linked in answer content, we want to switch them to using
# the file attachment system, so have to create the associated file and
# kaltura_media table entries for them.
#
# Here's a complex query that gets answers that has learning.video.ubc.ca links
# in them and don't have an associated Kaltura attachment. For our data, we can
# get away with just seeing if the answer doesn't have an attached file entry,
# so that's what what was implemented, but this query is documented for ref:
# select answer.id, answer.content, answer.file_id, file.kaltura_media_id from answer left join file on answer.file_id = file.id where answer.content like '%learning.video.ubc.ca%' and (answer.file_id is NULL or file.kaltura_media_id is NULL)
def migrateAnswerLinks(answers, oldToNewEntryIds, logfile):
    kClient = connectKalturaApi()
    regex = re.compile(r'https://learning.video.ubc.ca/media/([%\w+-]+?)/(\w+?)"')
    count = 0
    for answer in answers:
        count += 1
        msg(f'Answer {count}: {answer.id}', logfile)
        link = re.search(regex, answer.content)
        if not link:
            msg(f'Error: Answer {answer.id} content has no Kaltura link?', logfile)
            continue
        oldEntryId = link.group(2)
        newEntryId = oldToNewEntryIds[oldEntryId]
        newInfo = kClient.media.get(newEntryId, -1)
        videoName = newInfo.getName() + ".mp4"
        msg(f'  Video Name: {videoName}', logfile)
        msg(f'  Old Entry ID: {oldEntryId}', logfile)
        msg(f'  New Entry ID: {newEntryId}', logfile)
        msg(f'  Creating Kaltura File Entries...', logfile)
        kalturaMedia = KalturaMedia(
            user=answer.user,
            download_url=newInfo.getDownloadUrl(),
            # can't figure out how to get the original source extension, so
            # just assuming mp4
            file_name=videoName,
            service_url=KalturaCore.service_url(),
            partner_id=newInfo.getPartnerId(),
            player_id=KalturaCore.player_id(),
            entry_id=newEntryId
        )
        db.session.add(kalturaMedia)
        fileEntry = File(
            user=answer.user,
            kaltura_media=kalturaMedia,
            alias=videoName
        )
        db.session.add(fileEntry)
        answer.file = fileEntry
        db.session.commit()
        fileEntry.name = fileEntry.uuid + '.' + kalturaMedia.extension
        db.session.commit()
        msg(f'  Kaltura File Entries Created!', logfile)


# Some videos were linked in answer content, we want to switch them to using
# the file attachment system like all other kaltura media
@manager.command
def links(mappingCsv, noHeader=False, dryRun=False):
    ts = datetime.now().isoformat(timespec='seconds')
    logfile = open(f'kaltura-links-migration-log-{ts}.log', 'a')
    msg('Starting Kaltura links migration', logfile)
    oldToNewEntryIds = readMappingCsv(mappingCsv, noHeader)
    newToOldEntryIds = dict(map(reversed, oldToNewEntryIds.items()))
    needMigrationAnswers = []
    numInvalid = 0
    numAlreadyMigrated = 0
    numNoMapping = 0
    numTotal = 0
    answers = Answer.query \
        .filter(Answer.content.ilike('%learning.video.ubc.ca%')) \
        .filter(Answer.file_id.is_(None)) \
        .all()
    regex = re.compile(r'https://learning.video.ubc.ca/media/([%\w+-]+?)/(\w+?)"')
    # find out how much work needs to be done
    for answer in answers:
        numTotal += 1
        link = re.search(regex, answer.content)
        if not link:
            msg(f'Answer {answer.id} content has no Kaltura link?', logfile)
            numInvalid += 1
            continue
        entryId = link.group(2)
        if not entryId:
            msg(f'Answer {answer.id} Kaltura link has no entry ID', logfile)
            numInvalid += 1
        elif entryId in oldToNewEntryIds:
            msg(f"Migration needed on answer {answer.id}: Entry {entryId}", logfile)
            needMigrationAnswers.append(answer)
        elif entryId in newToOldEntryIds:
            # this is always 0, since answers with a file_id won't show up in
            # the query again
            msg(f"Already migrated answer {answer.id}: Entry {entryId}", logfile)
            numAlreadyMigrated += 1
        else:
            # didn't find a mapping, perhaps missing from migration?
            msg(f'No mapping for answer {answer.id}: Entry {entryId}', logfile)
            numNoMapping += 1
    # summarize what needs to be done
    summarize(len(needMigrationAnswers), numInvalid, numAlreadyMigrated,
              numNoMapping, numTotal, logfile)
    if dryRun:
        msg(f'*** Dry run completed, no changes were made ***', logfile)
    else:
        msg(f'Starting database session', logfile)
        migrateAnswerLinks(needMigrationAnswers, oldToNewEntryIds, logfile)
        msg(f'Committing to database', logfile)
        db.session.commit()
    logfile.close()


@manager.command
def migrate(mappingCsv, noHeader=False, dryRun=False):
    ts = datetime.now().isoformat(timespec='seconds')
    logfile = open(f'kaltura-migration-log-{ts}.log', 'a')
    msg('Starting Kaltura migration', logfile)
    oldToNewEntryIds = readMappingCsv(mappingCsv, noHeader)
    newToOldEntryIds = dict(map(reversed, oldToNewEntryIds.items()))
    invalidKalturaMedias = [] # can't be migrated, might as well delete
    needMigrationMedias = [] # needs to be migrated
    numAlreadyMigrated = 0
    numNoMapping = 0
    numTotal = 0
    kalturaMedias = KalturaMedia.query.all()
    # find out how much work needs to be done
    for kalturaMedia in kalturaMedias:
        numTotal += 1
        mediaId = kalturaMedia.id
        entryId = kalturaMedia.entry_id
        if not entryId:
            msg(f'Empty entry ID for id {mediaId}', logfile)
            invalidKalturaMedias.append(kalturaMedia)
        elif entryId in oldToNewEntryIds:
            msg(f"Migration needed for id {mediaId}: Entry {entryId}", logfile)
            needMigrationMedias.append(kalturaMedia)
        elif entryId in newToOldEntryIds:
            msg(f"Already migrated id {mediaId}: Entry {entryId}", logfile)
            numAlreadyMigrated += 1
        else:
            # didn't find a mapping, perhaps missing from migration?
            msg(f'No mapping for id {mediaId}: Entry {entryId}', logfile)
            numNoMapping += 1
    # summarize what needs to be done
    summarize(len(needMigrationMedias), len(invalidKalturaMedias),
              numAlreadyMigrated, numNoMapping, numTotal, logfile)
    # do the actual work in a transaction
    if dryRun:
        msg(f'*** Dry run completed, no changes were made ***', logfile)
    else:
        msg(f'Starting database session', logfile)
        deleteInvalidKalturaMedias(invalidKalturaMedias, logfile)
        migrateKalturaMedias(needMigrationMedias, oldToNewEntryIds, logfile)
        msg(f'Committing to database', logfile)
        db.session.commit()
    logfile.close()

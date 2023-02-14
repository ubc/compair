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


def migrateKalturaMedias(medias, oldToNewEntryIds, logfile):
    # connect to the Kaltura API
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

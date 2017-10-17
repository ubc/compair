import datetime
import copy
import random
from six.moves import range
import string

from compair import db
from data.factories import CourseFactory, UserFactory, UserCourseFactory, AssignmentFactory, \
    AnswerFactory, CriterionFactory, ComparisonFactory, AssignmentCriterionFactory, FileFactory, \
    AssignmentCommentFactory, AnswerCommentFactory, AnswerScoreFactory, ComparisonExampleFactory, \
    LTIConsumerFactory, LTIContextFactory, LTIResourceLinkFactory, \
    LTIUserFactory, LTIUserResourceLinkFactory, ThirdPartyUserFactory

from compair.models import PairingAlgorithm, SystemRole, CourseRole, Comparison, \
    AnswerComment, AnswerCommentType, Answer, WinningAnswer

def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class DefaultFixture(object):
    ROOT_USER_ID = 1
    ROOT_USER = None
    DEFAULT_CRITERION = None

    def __init__(self):
        DefaultFixture.ROOT_USER = UserFactory(
            id=DefaultFixture.ROOT_USER_ID, #need to have a fixed id from demos
            username='root',
            password='password',
            firstname="System",
            lastname="Administrator",
            email=None,
            system_role=SystemRole.sys_admin,
            displayname='root',
            student_number=None
        )

        DefaultFixture.DEFAULT_CRITERION = CriterionFactory(
            name="Which is better?",
            description="<p>Choose the response that you think is the better of the two.</p>",
            public=True,
            user=DefaultFixture.ROOT_USER
        )

class DemoDataFixture(object):
    DEFAULT_COURSE_ID = 1
    DEFAULT_ASSIGNMENT_IDS = [1,2]
    DEFAULT_INSTRUCTOR_ID = 2
    DEFAULT_STUDENT_IDS = range(3,33) # student ids are 3 to 32
    DEFAULT_COURSE_USERS = range(2,33) # instructor + students

    def __init__(self):
        now = datetime.datetime.utcnow()

        # create instructor
        instructor = UserFactory(
            id=DemoDataFixture.DEFAULT_INSTRUCTOR_ID, #need to have a fixed ids from demos
            username="instructor1",
            password="demo",
            firstname="Instructor",
            lastname="One",
            email=None,
            system_role=SystemRole.instructor,
            displayname="Instructor One",
            student_number=None
        )
        db.session.add(instructor)
        db.session.commit()

        # create course
        course = CourseFactory(
            id=DemoDataFixture.DEFAULT_COURSE_ID, #need to have a fixed ids from demos
            name="ComPAIR Demo Course",
            year=now.year,
            term="W1",
        )
        db.session.add(course)
        db.session.commit()

        # enroll instructor in course
        db.session.add(UserCourseFactory(
            course=course,
            user=instructor,
            course_role=CourseRole.instructor
        ))
        db.session.commit()

        # create students
        students = []
        for index, student_id in enumerate(DemoDataFixture.DEFAULT_STUDENT_IDS):
            student = UserFactory(
                id=student_id, #need to have a fixed ids from demos
                username="student"+str(index+1),
                password="demo",
                firstname="Student",
                lastname=str(index+1),
                email=None,
                system_role=SystemRole.student,
                displayname="student_"+random_generator(),
                student_number="10000000"[ : - len(str(index+1))] + str(index+1)
            )
            students.append(student)
            db.session.add(student)
            db.session.add(UserCourseFactory(
                course=course,
                user=student,
                course_role=CourseRole.student
            ))
        db.session.commit()

        # create simple assignment criteria
        criterion1 = CriterionFactory(
            user=instructor,
            name="Which interests you more?",
            description="Pick which opener provides a stronger pull for you.",
            default=True
        )
        criterion2 = CriterionFactory(
            user=instructor,
            name="Which is better written?",
            description="Pick which opener is better written.",
            default=True
        )
        db.session.add(criterion1)
        db.session.add(criterion2)
        db.session.commit()

        # create simple assignment
        simple_assignment = AssignmentFactory(
            id=DemoDataFixture.DEFAULT_ASSIGNMENT_IDS[0], #need to have a fixed id from demos
            user=instructor,
            course=course,
            name="Start a short story",
            description="<p>Simple assignment in comparison period</p><p>Provide the proposed opening sentence of your short story (one sentence only), as assigned in last week's class. Then provide feedback and evaluations of three pairs of your peers' openers. (You will in turn receive peer feedback on your own opener.)</p>",
            answer_start=(now - datetime.timedelta(days=14)),
            answer_end=(now - datetime.timedelta(days=7)),
            compare_start=(now - datetime.timedelta(days=5)),
            compare_end=(now + datetime.timedelta(days=12)),
            number_of_comparisons=3,
            students_can_reply=True,
            enable_self_evaluation=False,
            pairing_algorithm=PairingAlgorithm.adaptive_min_delta,
            educators_can_compare=True
        )
        db.session.add(simple_assignment)
        db.session.add(AssignmentCriterionFactory(
            criterion=criterion1,
            assignment=simple_assignment,
            position=0
        ))
        db.session.add(AssignmentCriterionFactory(
            criterion=criterion2,
            assignment=simple_assignment,
            position=1
        ))
        db.session.commit()

        # create simple assignment
        answer_text = [
            "<p>Everyone deserves to know a little something about where they come from, but I don't know any thing.</p>",
            "<p>Like water and oil, Sarah and Bryan did not mix well, but that didn't stop their wedding from happening anyway.</p>",
            "<p>In the years to come, Chester would look back on this moment and laugh, but on that hot sunny afternoon, hanging by his torn shorts from a jagged tree branch, feeling the sun burn his exposed lower back (and more!), absolutely nothing seemed funny in life at all.</p>",
            "<p>The final countdown ended, and Geraldine sped off across the grassy lawn at a blazing pace, her eyes focused only on the golden cup at the other end of the yard.</p>",
            "<p>Her hand had barely grazed the wet copper penny on the ground when the whole world instantly fell away.</p>",
            "<p>The doll stared creepily at Renauld through the cracked and foggy display window, daring him to buy it.</p>",
            "<p>On that fateful autumn morning, the birds were as silent as the unmoving body in front of her.</p>",
            "<p>I never believed in true love until I met the robot posing as my next door neighbour.</p>",
            "<p>Just like with the grocery store and bellies, Mama always said not to go into a wedding shop on an empty budget.</p>",
            "<p>Jared used to think any problem could be solved by drinking, fighting, or sleeping (and a combination of all three would do for the hardest of problems), but that was before the Big Unsolvable Problem showed up on his doorstep.</p>",
            "<p>Once upon a time, an ugly boy met a beautiful girl in a whimsical woodsy park, and that my friends is where the adventure began.</p>",
            "<p>No one knew what Barney really kept in the old rotted shack behind his house except Lisa.</p>",
            "<p>It was a dark and stormy night, the kind of dark and stormy they only write about in stories like these.</p>",
            "<p>Few things are as important in Alfalfian life as remembering where you hid your leprechaun detector, but George could not for the life of him recall what had happened to his.</p>",
            "<p>Not enough people understand about skunks or how dangerous they can be when let loose in your parent's basement.</p>",
            "<p>Five years ago, I entered the subway as Sally Montegomery and emerged as Salvation, the reluctant (if effective) crime-fighting subway superhero.</p>",
            "<p>Two dogs could not be more different than tiny, cuddly Cupcake and giant, intimidating Bull, but together they managed to save half the neighbourhood kids from a horrible, unspeakable monster one heroic summer.</p>",
            "<p>The fall out the window went on forever, even though he only fell about six feet, but Nathan knew it would change his life for every day after.</p>",
            "<p>Eve was the Chosen one in her family, a fact she met with equal parts pride and dread.</p>",
            "<p>A tiny purple house stood at the end of the quiet street Janet grew up on, and no one who went into it ever seemed to come back out.</p>",
            "<p>I've always gotten along well with snakes, no matter their size, temperament, or thoughts on politics.</p>",
            "<p>\"I know what haunts you,\" an old woman whispered to Josie.</p>",
            "<p>It wasn't the best of times, but it was far from the worst of times either, and that's what made life so damn frustrating for Kenny.</p>",
            "<p>I've always shared stories of my day with my teddy bear, but the day I knew I'd gone crazy was when he finally talked back.</p>",
            "<p>The impact of the oncoming semi slammed me into the seat back in front of me, but the violent spinout that followed threw me even harder into the side door before I could catch my breath to scream.</p>",
            "<p>Jelly donuts were never Detective John P. Lawson's thing.</p>",
            "<p>\"Do you want to be ordinary for the entire rest of your life?\" she asked me.</p>",
            "<p>You wouldn't believe how much it costs to buy and maintain a rainbow.</p>"
        ]

        for index, text in enumerate(answer_text):
            db.session.add(AnswerFactory(
                assignment=simple_assignment,
                user=students[index],
                content=text,
                draft=False,
                created=(now - datetime.timedelta(days=12) + datetime.timedelta(minutes=5*index))
            ))
        db.session.commit()

        criterion3 = CriterionFactory(
            user=instructor,
            name="Which is better?",
            description="Pick which film is overall better.",
            default=True
        )
        db.session.add(criterion3)
        db.session.commit()

        # create complex assignment
        complex_assignment = AssignmentFactory(
            id=DemoDataFixture.DEFAULT_ASSIGNMENT_IDS[1], #need to have a fixed id from demos
            user=instructor,
            course=course,
            name="What is the best film of all time?",
            description="""
            <p>Assignment after comparison period (with external links to images and videos)</p>
            <p>Share the best film ever produced.
            Include a short summary (one sentence) and include a compelling clip or screen from the film.
            Then provide reviews and evaluations on three pairs of your peers' chosen film.
            (You will in turn receive peer feedback on your own chosen film.)</p>
            """,
            answer_start=(now - datetime.timedelta(days=30)),
            answer_end=(now + datetime.timedelta(days=120)),
            compare_start=(now - datetime.timedelta(days=30)),
            compare_end=(now + datetime.timedelta(days=120)),
            number_of_comparisons=3,
            students_can_reply=True,
            enable_self_evaluation=True,
            pairing_algorithm=PairingAlgorithm.adaptive_min_delta,
            educators_can_compare=True,
            rank_display_limit=10
        )
        db.session.add(complex_assignment)
        db.session.add(AssignmentCriterionFactory(
            criterion=criterion3,
            assignment=complex_assignment,
            position=0
        ))
        db.session.commit()

        complex_assignment.assignment_criteria.reorder()

        # help comments
        db.session.add(AssignmentCommentFactory(
            user=students[0],
            assignment=complex_assignment,
            content="<p>How should we format our answers?</p>",
            created=(now - datetime.timedelta(days=29))
        ))
        db.session.add(AssignmentCommentFactory(
            user=instructor,
            assignment=complex_assignment,
            content="""
            <p>You should format them like this:</p>
            <p>Title (Year). Summary.</p>
            <p>Link</p>
            """,
            created=(now - datetime.timedelta(days=29) + datetime.timedelta(minutes=30))
        ))
        db.session.commit()

        answer_index = 0
        answer_comments = {}
        #0
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Wizard of Oz (1939). An absolute masterpiece whose groundbreaking visuals and deft storytelling are still every bit as resonant, The Wizard of Oz is a must-see film for young and old.</p>
            <p><a href="http://cdn2.hubspot.net/hubfs/454819/wizard_of_oz_man_behind_curtain_bluesnap.gif" target="_blank">Man behind the curtain</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Absolutely! how come I didn't think of this! One of the classics.</p>",
            "<p>Any reason to show your children The Wizard of Oz on a big screen seems like a good one.</p>",
            "<p>A work of almost staggering iconographic, mythological, creative and simple emotional meaning, at least for American audiences, this is one vintage film that fully lives up to its classic status.</p>",
            "<p>Remains the weirdest, scariest, kookiest, most haunting and indelible kid-flick-that's- really-for-adults ever made in Hollywood.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #1
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Citizen Kane (1941). Remarkably creative film is inventive both in story and visual style.</p>
            <p><a href="https://www.youtube.com/watch?v=BvkAoQsfDOM" target="_blank">Watch it</a> if you haven't already (its public domain)</p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Welles has found the screen as effective for his unique showmanship as radio and the theatre.</p>",
            "<p>It can be classified as, in a number of aspects, one of the most arresting pictures ever produced.</p>",
            "<p>What's striking now is how utterly modern it is in structure.</p>",
            "<p>Loved this movie.</p>",
            "<p>Many of the novel techniques Welles developed with cinematographer Gregg Toland were calculated to offer new angles on film space.</p>",
            "<p>Citizen Kane may very well be the most talked-about movie in history.</p>",
            "<p>Great choice in film</p>",
            "<p>Really good choice in film.</p>",
        ]
        answer_index+=1

        #2
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Third Man (1949). This atmospheric thriller is one of the undisputed masterpieces of cinema, and boasts iconic performances from Joseph Cotten and Orson Welles.</p>
            <p><a href="https://www.youtube.com/watch?v=F-QWLAndD1E" target="_blank">https://www.youtube.com/watch?v=F-QWLAndD1E</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>It's an exciting experience, dazzling and entertaining and thought-provoking.</p>",
            "<p>The Third Man is a movie of sobering pleasures.</p>",
            "<p>As powerful and original now as it was in 1949.</p>",
            "<p>One of British cinema's most enduring and atmospheric thrillers. A genuine and endlessly rewatchable classic.</p>",
            "<p>It transformed the way I looked at the world.</p>",
            "<p>This is a unique classic.</p>",
            "<p>A little dated for my tastes but still great.</p>",
            "<p>Absolutely! how come I didn't think of this! One of the classics.</p>",
        ]
        answer_index+=1

        #3
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Mad Max: Fury Road (2015). With exhilarating action and a surprising amount of narrative heft, Mad Max: Fury Road brings George Miller's post-apocalyptic franchise roaring vigorously back to life.</p>
            <p><a href="http://www.filmblerg.com/wp-content/uploads/2015/05/Mad-Max-Fury-Road-lovely-day.png" target="_blank">Mad Max pic</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Happy end of the world.</p>",
            "<p>Believe all the hype: This movie will melt your face off. </p>",
            "<p>A gorgeous, scrap-metal demolition derby of a popcorn picture.</p>",
            "<p>Miller has the dubious distinction of essentially creating the post-apocalyptic action genre, and in this film, set some 40 years after the fall of the world, he outdoes himself.</p>",
            "<p>Two hours of action scenes that are well crafted and entirely lacking in suspense, and with some clever but fake-looking special effects.</p>",
            "<p>An operatic extravaganza of thrilling action and nearly non-stop mayhem ... exhilarating, deranged and exhausting in almost equal measures.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #4
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>All About Eve (1950). Smart, sophisticated, and devastatingly funny, All About Eve is a Hollywood classic that only improves with age.</p>
            <p><a href="https://upload.wikimedia.org/wikipedia/commons/a/af/All_About_Eve_trailer_%281950%29.webm" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>All About Eve is not only a brilliant and clever portrait of an actress, it is a downright funny film, from its opening scene to the final fadeout.</p>",
            "<p>Joseph Mankiewicz was Hollywood's midcentury master of comic drama, and All About Eve, from 1950, was one of his signal achievements.</p>",
            "<p>The Zanuck production investiture is plush in every department.</p>",
            "<p>Mankiewicz's flair for dialog is so perfected that all three actresses shoot fireworks whenever they open their mouths.</p>",
            "<p>Is there anyone alive who hasn't seen All About Eve -- anyone who doesn't love movies, that is?</p>",
            "<p>Mankiewicz's 1950 gem is a wickedly cynical cocktail of laughter and deceit in which everyone has an angle to play.</p>",
            "<p>Absolutely! how come I didn't think of this! One of the classics.</p>",
            "<p>Really good choice in film.</p>",
        ]
        answer_index+=1

        #5
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Cabinet of Dr. Caligari (1920). Arguably the first true horror film, The Cabinet of Dr. Caligari set a brilliantly high bar for the genre -- and remains terrifying nearly a century after it first stalked the screen.</p>
            <p><a href="http://theredlist.com/media/upload/2013/09/12/1378996191-5231cfdfbfe8c-020-the-cabinet-of-dr-caligari.jpg" target="_blank">Sceen</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>A case can be made that Caligari was the first true horror film.</p>",
            "<p>This is more than just a textbook classic; the narrative frame creates ambiguities that hold certain elements of the story in disturbing suspension. A one-of-a-kind masterpiece.</p>",
            "<p>Undoubtedly one of the most exciting and inspired horror movies ever made.</p>",
            "<p>Robert Wiene has made perfect use of settings designed by Hermann Warm, Walter Reimann and Walter Roehrig, settings that squeeze and turn and adjust the eye and through the eye the mentality.</p>",
            "<p>A foundational nightmare vision.</p>",
            "<p>A classic. Visually stunning and more experimental than anything coming out today.</p>",
            "<p>Great choice in film</p>",
            "<p>Loved this movie.</p>",
        ]
        answer_index+=1

        #6
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Inside Out (2015). Inventive, gorgeously animated, and powerfully moving, Inside Out is another outstanding addition to the Pixar library of modern animated classics.</p>
            <p><a href="https://whatisupcoming.files.wordpress.com/2015/02/inside-out-movie-2015.jpg" target="_blank">Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>This is a movie that dares to explore existential crises, in the middle of the summer, in an animated movie that's aimed at the whole family</p>",
            "<p>On the scale of inventiveness, \"Inside Out\" will be hard to top this year. As so often with Pixar, you feel that you are visiting a laboratory crossed with a rainbow.</p>",
            "<p>Inside Out is the best American-produced animated film we have seen in many summers and deserves to be recognized as such.</p>",
            "<p>Inside Out is the first psychological thriller that's fun for the whole family. Really psychological. And really fun.</p>",
            "<p>Inside Out isn't just a sign of renewed youth from Pixar. It's the reason Pixar exists.</p>",
            "<p>Only in the medium of animation could a conceit as elaborate as Inside Out's be dramatized, and only animation this well-designed and executed could bring such a story so vibrantly to life.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #7
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Get Out (2017). Funny, scary, and thought-provoking, Get Out seamlessly weaves its trenchant social critiques into a brilliantly effective and entertaining horror/comedy thrill ride.</p>
            <p><a href="https://www.youtube.com/watch?v=DzfpyUB60YY" target="_blank">Best trailer ever</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Well cast and slickly edited... situations are horrific in their banality... who knew teacups could be sinister?</p>",
            "<p>Jordan Peele's semi-parodic horror film Get Out has a complexity worthy of its historical moment.</p>",
            "<p>Towards the end, it all gets a little overwrought. But, on the whole, what a clever, provocative and entertaining film this is in the way it pokes and prods at the emotive issue of race relations while mixing up so many genres.</p>",
            "<p>Kaluuya brings a wry intelligence his role as the straight man to the films' many eccentric characters.</p>",
            "<p>It will probably end up being the best horror movie of the year, and easily one of the best of the past five years.</p>",
            "<p>Jordan Peele is known for being really good at comedy, and now it turns out he's really good at horror too.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #8
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Godfather (1972). One of Hollywood's greatest critical and commercial successes, The Godfather gets everything right; not only did the movie transcend expectations, it established new benchmarks for American cinema.</p>
            <p><a href="http://orig06.deviantart.net/6b48/f/2015/044/3/a/the_godfather__1972__fan_made_movie_poster_by_k_hosni-d8hsp14.jpg" target="_blank">Movie Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>This is a curious film. One comes to understand, even to condone, the activities of the Godfather and his clan.</p>",
            "<p>The Godfather is overflowing with life, rich with all the grand emotions and vital juices of existence, up to and including blood.</p>",
            "<p>Brando's triumph and fascination is less that of an actor of parts than of a star galaxy of myths. </p>",
            "<p>As filmmaking and storytelling, 'The Godfather' remains a bravura piece of work, its set pieces, dialogue and performances entrenched cinematic icons.</p>",
            "<p>The ultimate family film.</p>",
            "<p>In scene after scene ... Coppola crafted an enduring, undisputed masterpiece.</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>",
        ]
        answer_index+=1

        #9
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Metropolis (1927). A visually awe-inspiring science fiction classic from the silent era.</p>
            <p><a href="https://twscritic.files.wordpress.com/2012/12/metropolis-scientist.jpg" target="_blank">Powerful scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Lang's allegory of allegories posits humanity's progress as a collision not just of labor and management but of technology and sorcery</p>",
            "<p>Each frame of this classic is drop-dead stunning.</p>",
            "<p>Metropolis remains the benchmark of agenda-driven extravaganzas, stirring and fun in the right spots.</p>",
            "<p>Here is the starting-point of so much modern cinema.</p>",
            "<p>A perfect gateway drug for old movies.</p>",
            "<p>Every dystopian vision owes a debt of gratitude to Metropolis.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #10
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Modern Times (1936). A slapstick skewering of industrialized America, Modern Times is as politically incisive as it is laugh-out-loud hilarious.</p>
            <p><a href="http://www.teachwithmovies.org/guides/modern-times-files/screen.jpg" target="_blank">Funny scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>One of the many remarkable things about Charlie Chaplin is that his films continue to hold up, to attract and delight audiences.</p>",
            "<p>Chaplin's political and philosophical naivety now seems as remarkable as his gift for pantomime.</p>",
            "<p>Good physical comedy will always be funny, and Chaplin was a master.</p>",
            "<p>Modern Times is an ungainly masterpiece, but Chaplin's ungainliness is something one can grow fond of.</p>",
            "<p>The picture is a two-hour almost continuous gale of laughter with sidesplitting gags generously distributed throughout the five major sequences and the several minor ones.</p>",
            "<p>The mechanical feeding sequence in Modern Times is probably the funniest routine in cinema history.</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #11
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>E.T. The Extra-Terrestrial (1982). Playing as both an exciting sci-fi adventure and a remarkable portrait of childhood, Steven Spielberg's touching tale of a homesick alien remains a piece of movie magic for young and old.</p>
            <p><a href="https://de1imrko8s7v6.cloudfront.net/movies/posters/ET-the-Extra-Terrestrial-movie-poster_1369930604.jpg" target="_blank">Memerable poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>E.T. is essentially a spiritual autobiography, a portrait of the filmmaker as a typical suburban kid set apart by an uncommonly fervent, mystical imagination. It comes out disarmingly funny, spontaneous, bighearted.</p>",
            "<p>It holds up beautifully.</p>",
            "<p>Spielberg left it open for all of us. That's the sign of a great filmmaker: He only explains what he has to explain.</p>",
            "<p>A contemporary classic.</p>",
            "<p>What's perhaps most amazing about E.T., what distinguishes it from many of the other fantasy films of its era, is its ability to put an audience under a spell of childlike wonderment without infantilizing it.</p>",
            "<p>Though marred by Spielberg's usual carelessness with narrative points, the film alternates sweetness and sarcasm with enough rhetorical sophistication to be fairly irresistible.</p>",
            "<p>Absolutely! how come I didn't think of this! One of the classics.</p>",
            "<p>Really good choice in film.</p>",
        ]
        answer_index+=1

        #12
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Singin' in the Rain (1952). Clever, incisive, and funny, Singin' in the Rain is a masterpiece of the classical Hollywood musical.</p>
            <p><a href="https://www.youtube.com/watch?v=D1ZYhVpdXbQ" target="_blank">One of the most memorable musical scenes</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Singin' in the Rain is another mighty fine MGM Technicolor musical comedy produced by Arthur Freed whose An American in Paris copped seven Academy awards last week.</p>",
            "<p>One of the shining glories of the American musical.</p>",
            "<p>If you've never seen it and don't, you're bonkers.</p>",
            "<p>The ultimate nostalgic source text is itself a pomo homage to a lost moment.</p>",
            "<p>There is no movie musical more fun than Singin' in the Rain, and few that remain as fresh over the years.</p>",
            "<p>A fancy package of musical entertainment with wide appeal and bright grossing prospects.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #13
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>It Happened One Night (1934). Capturing its stars and director at their finest, It Happened One Night remains unsurpassed by the countless romantic comedies it has inspired.</p>
            <p><a href="http://cdn3-www.comingsoon.net/assets/uploads/1970/01/file_599350_it-happened-one-night-best-movies.jpg" target="_blank">Film Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>It's probably more historically important than it is a masterpiece (the last 20 minutes take the missed conections and misunderstandings an inch too far), but it's still very easy to fall in love with.</p>",
            "<p>This is Capra at his best, very funny and very light, with a minimum of populist posturing.</p>",
            "<p>It Happened One Night is a good piece of fiction, which, with all its feverish stunts, is blessed with bright dialogue and a good quota of relatively restrained scenes.</p>",
            "<p>One of those stories that without a particularly strong plot manages to come through in a big way, due to the acting, dialog, situations and direction.</p>",
            "<p>It Happened One Night is a good piece of fiction, which, with all its feverish stunts, is blessed with bright dialogue and a good quota of relatively restrained scenes.</p>",
            "<p>Instead of attempting a journalistic study of bus-travel, regularly punctuated by comic touches, Director Frank Capra and Robert Riskin who adapted Samuel Hopkins Adams' story, fused the two.</p>",
            "<p>Never heard of this one before. Interesting choice.</p>",
            "<p>Loved this movie.</p>",
        ]
        answer_index+=1

        #14
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Casablanca (1942). An undisputed masterpiece and perhaps Hollywood's quintessential statement on love and romance, Casablanca has only improved with age, boasting career-defining performances from Humphrey Bogart and Ingrid Bergman.</p>
            <p><a href="https://www.youtube.com/watch?v=BkL9l7qovsE" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>While the future was uncertain, the resolute characters of this exquisite wartime drama found peace through love and resistance.</p>",
            "<p>Certainly a more accomplished cast of players cannot be imagined, and their direction by Michael Curtiz is inspired. </p>",
            "<p>Nobody lights a torch like Ingrid Bergman's Ilsa or carries one like Humphrey Bogart's Rick.</p>",
            "<p>The greatest pleasure anyone can derive from this movie comes through simply watching it.</p>",
            "<p>Seeing the film over and over again, year after year, I find it never grows over-familiar. It plays like a favorite musical album; the more I know it, the more I like it.</p>",
            "<p>Part of what makes this wartime Hollywood drama (1942) about love and political commitment so fondly remembered is its evocation of a time when the sentiment of this country about certain things appeared to be unified.</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #15
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Boyhood (2014). Epic in technical scale but breathlessly intimate in narrative scope, Boyhood is a sprawling investigation of the human condition.</p>
            <p><a href="https://www.youtube.com/watch?v=IiDztHS3Wos" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Calling it a sum of its parts can be a backhanded compliment, but it feels like especially worthy praise for Boyhood, considering how much went into making it feel whole. </p>",
            "<p>While everything about Boyhood is done with extraordinary care, the master stroke was clearly the casting, 13 years ago, of a little Texas boy named Ellar Coltrane.</p>",
            "<p>It's like a time-lapse photo of an expanding consciousness.</p>",
            "<p>Boyhood is proof that a strange magic can still bloom amidst the tragedy that buffets human life.</p>",
            "<p>An exceptionally well-crafted coming-of-age story.</p>",
            "<p>The closest thing to a lived life that fictional cinema has yet produced.</p>",
            "<p>Great choice in film</p>",
            "<p>Never heard of this one before. Interesting choice.</p>",
        ]
        answer_index+=1

        #16
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Laura (1944). A psychologically complex portrait of obsession, Laura is also a deliciously well-crafted murder mystery.</p>
            <p><a href="https://s-media-cache-ak0.pinimg.com/originals/46/1b/e9/461be9d07ab64a9e6c6f59297762b503.jpg" target="_blank">Important scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Few movies make you feel dirtier, and so perversely grateful for the pleasure.</p>",
            "<p>Less a crime film than a study in levels of obsession, Laura is one of those classic works that leave their subject matter behind and live on the strength of their seductive style.</p>",
            "<p>A hypnotic and deathlessly interpretable experience.</p>",
            "<p>The plot is deliberately perfunctory, the people deliciously perverse, and the mise-en-scene radical.</p>",
            "<p>The picture on the whole is close to being a top-drawer mystery.</p>",
            "<p>The materials of a B-grade crime potboiler are redeemed by Waldo Lydecker, walking through every scene as if afraid to step in something.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #17
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>A Hard Day's Night (1964). A Hard Day's Night, despite its age, is still a delight to watch and has proven itself to be a rock-and-roll movie classic.</p>
            <p><a href="https://upload.wikimedia.org/wikipedia/en/4/47/A_Hard_Days_night_movieposter.jpg" target="_blank">Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>The movie never feels like a nostalgia trip. It moves, breathes and sings with life.</p>",
            "<p>The whole movie is an ecstatic mix of serendipity and invention. The Beatles were ready for their cinematic breakthrough.</p>",
            "<p>Let's talk about joy, and about wistfulness, because one so often trails the other, and both are woven into the DNA of A Hard Day's Night.</p>",
            "<p>The mop-tops are likeably relaxed, with Lennon offering a few welcome moments of his dry, acerbic wit.</p>",
            "<p>Not only has this film not dated, it may even look fresher than it did in 1964; the zigzag cutting and camera moves, the jaunty ironies and pop-celebrity playfulness, are all standard issue now on MTV and its offspring.</p>",
            "<p>The music video by which all other music videos must be judged. And none top it</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #18
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Nosferatu, a Symphony of Horror (1922). One of the silent era's most influential masterpieces, Nosferatu's eerie, gothic feel -- and a chilling performance from Max Schreck as the vampire -- set the template for the horror films that followed.</p>
            <p><a href="https://i.ytimg.com/vi/lhWwUQw-sNk/hqdefault.jpg" target="_blank">Awesome scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>So this is it: ground zero, the birth of horror cinema.</p>",
            "<p>Never mind that much of the story of this first important screen version of the Dracula legend seems corny and dated, for what counts is its atmosphere and its images, which are timeless in their power.</p>",
            "<p>It's not just a great horror movie. It's a poem of horror, a symphony of dread, a film so rapt, mysterious and weirdly lovely it haunts the mind long after it's over.</p>",
            "<p>The film shows Murnau's uncanny mixture of expressionism and location shooting at its finest.</p>",
            "<p>A masterpiece of the German silent cinema and easily the most effective version of Dracula on record.</p>",
            "<p>It doesn't scare us, but it haunts us. It shows not that vampires can jump out of shadows, but that evil can grow there, nourished on death.</p>",
            "<p>Great choice in film</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #19
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Snow White and the Seven Dwarfs (1937). With its involving story and characters, vibrant art, and memorable songs, Snow White and the Seven Dwarfs set the animation standard for decades to come.</p>
            <p><a href="https://i.jeded.com/i/snow-white-and-the-seven-dwarfs.31581.jpg" target="_blank">Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>The film is as charming as it is novel in conception and execution and it is so bound to appeal as strongly to grown-ups as to youngsters.</p>",
            "<p>To say of Snow White and the Seven Dwarfs that it is among the genuine artistic achievements of this country takes no great daring.</p>",
            "<p>So perfect is the illusion, so tender the romance and fantasy, so emotional are certain portions when the acting of the characters strikes a depth comparable to the sincerity of human players, that the film approaches real greatness.</p>",
            "<p>To one degree or another, every animated feature made since owes it something.</p>",
            "<p>Like many of the Disney films, from Pinocchio to Fantasia, this film is a cinematic rite of passage -- for children and adults.</p>",
            "<p>The animation itself is top-notch, and in a number of darker sequences (Snow White's terrified entry into the forest, for example), Disney's adoption of Expressionist visual devices makes for genuinely powerful drama.</p>",
        ]
        answer_index+=1

        #20
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Battle of Algiers (1967). A powerful, documentary-like examination of the response to an occupying force, The Battle of Algiers hasn't aged a bit since its release in 1966.</p>
            <p><a href="https://assets.mubi.com/images/film/248/image-w856.jpg?1485452547" target="_blank">Great scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>It uses realism as an effect, documentary as a style. You feel that you're really there, and you can't help but be moved.</p>",
            "<p>It neither demonizes nor lionizes either side of the conflict, aiming for just-the-ugly facts objectivity. Nobody who sees it is likely to feel comforted, or even vindicated. The emotion it most frequently and fervently inspires is sorrow.</p>",
            "<p>The film is not just a relentlessly gripping entertainment but also a cinematic Rorschach blot, a moral miasma that tosses our sympathies this way and that.</p>",
            "<p>Both a how-to manual for guerrilla terrorism and a cautionary tale about how to fight it. It's also quite possibly the finest war film ever made.</p>",
            "<p>What lessons a modern viewer can gain from the film depends on who is watching and what they want to see.</p>",
            "<p>It's as fresh and suspenseful as anything before or since.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #21
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>North by Northwest (1959). Gripping, suspenseful, and visually iconic, this late-period Hitchcock classic laid the groundwork for countless action thrillers to follow.</p>
            <p><a href="https://www.youtube.com/watch?v=9NPI9QeeDDc" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Hitchcock breezes through a tongue-in-cheek, nightmarish plot with a lightness of touch that's equalled by a charming performance from Grant.</p>",
            "<p>A great film, and certainly one of the most entertaining movies ever made, directed by Alfred Hitchcock at his peak.</p>",
            "<p>At times it seems Hitchcock is kidding his own penchant for the bizarre, but this sardonic attitude is so deftly handled it only enhances the thrills.</p>",
            "<p>Of course, the hallmark of North by Northwest is the way in which Hitchcock develops tension.</p>",
            "<p>Hitchcock's ultimate wrong-man comedy.</p>",
            "<p>Smoothly troweled and thoroughly entertaining.</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #22
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Repulsion (1965). Roman Polanski's first English film follows a schizophrenic woman's descent into madness, and makes the audience feel as claustrophobic as the character.</p>
            <p><a href="https://images-na.ssl-images-amazon.com/images/M/MV5BNDRjNmRlMWQtZTNiZS00MzJiLTlkOGMtMDJlNDBlZDlkM2Y5XkEyXkFqcGdeQXVyMzU4ODM5Nw@@._V1_.jpg" target="_blank">Nice scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Roman Polanski's first English-language film is still a creepy little horror masterpiece.</p>",
            "<p>At second glance, or as often as a moviegoer can bear to peek through his knotted fingers, it is a Gothic horror story, a classic chiller of the Psycho school and approximately twice as persuasive.</p>",
            "<p>Roman Polanski's first film in English is still his scariest and most disturbing.</p>",
            "<p>Still perhaps Polanski's most perfectly realised film, a stunning portrait of the disintegration, mental and emotional, of a shy young Belgian girl (Deneuve) living in London.</p>",
            "<p>Prepare yourself to be demolished when you go to see it -- and go you must, because it's one of those films everybody will soon be buzzing about.</p>",
            "<p>Repulsion is a frightening, fiercely entertaining experience that holds up to time.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #23
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Gravity (2013). Gravity is an eerie, tense sci-fi thriller that's masterfully directed and visually stunning.</p>
            <p><a href="http://m.aceshowbiz.com/webimages/still/gravity-poster02.jpg" target="_blank">Powerful poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>Believe the hype: Gravity is as jaw-droppingly spectacular as you've heard - magnificent from a technical perspective but also a marvel of controlled acting and precise tone. </p>",
            "<p>Unfolding as a series of terrifying object lessons in Newtonian physics, the movie lends new meaning to the phrase \"spatial geometry.\"</p>",
            "<p>Gravity is not a film of ideas, like Kubrick's techno-mystical 2001, but it's an overwhelming physical experience -- a challenge to the senses that engages every kind of dread.</p>",
            "<p>Nerve-racking, sentimental and thrilling, Gravity honors terra firma even as it reaches for the stars with Sandra Bullock and George Clooney.</p>",
            "<p>The most surprising and impressive thing about \"Gravity\" isn't its scale, its suspense, or its sense of wonder; it's that, in its heart, it is not primarily a film about astronauts, or space, or even a specific catastrophe.</p>",
            "<p>This is one of the most stunning visual treats of the year and one of the most unforgettable thrill rides in recent memory.</p>",
            "<p>Great choice in film</p>",
            "<p>Loved this movie.</p>",
        ]
        answer_index+=1

        #24
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Maltese Falcon (1941). Suspenseful, labyrinthine, and brilliantly cast, The Maltese Falcon is one of the most influential noirs -- as well as a showcase for Humphrey Bogart at his finest.</p>
            <p><a href="http://nickyarborough.com/wp-content/uploads/2015/09/Poster-Maltese-Falcon-The-1941_02.jpg" target="_blank">Poster</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>The Maltese Falcon is the first crime melodrama with finish, speed and bang to come along in what seems ages.</p>",
            "<p>The Maltese Falcon is among the most important and influential movies to emerge from the Hollywood system -- as significant in some ways as its contemporary, Citizen Kane.</p>",
            "<p>Filmed almost entirely in interiors, it presents a claustrophobic world animated by betrayal, perversion and pain.</p>",
            "<p>Mr. Huston gives promise of becoming one of the smartest directors in the field.</p>",
            "<p>Among the movies we not only love but treasure, The Maltese Falcon stands as a great divide.</p>",
            "<p>Frighteningly good evidence that the British (Alfred Hitchcock, Carol Reed, et al.) have no monopoly on the technique of making mystery films.</p>",
            "<p>Loved this movie.</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #25
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>12 Years a Slave (2013). It's far from comfortable viewing, but 12 Years a Slave's unflinchingly brutal look at American slavery is also brilliant -- and quite possibly essential -- cinema.</p>
            <p><a href="https://www.youtube.com/watch?v=z02Ie8wKKRg" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>It speaks to the courage and resilience of one man, the savagery of many, and the potential, for both good and for ill, in us all.</p>",
            "<p>The cumulative emotional effect is devastating: the final scenes are as angry, as memorable, as overwhelming as anything modern cinema has to offer.</p>",
            "<p>So overpowering is this film's simple, horrible, and almost entirely true story that it's hard to get enough distance on 12 Years a Slave to poke at its inner workings.</p>",
            "<p>Every scene of 12 Years a Slave, and almost every shot, conveys some penetrating truth about America's original sin.</p>",
            "<p>The film is both brutal to watch and stunning to contemplate, powerfully challenging audiences - particularly white audiences - to examine their consciences.</p>",
            "<p>12 Years a Slave is at times difficult to watch but always impossible to turn away from.</p>",
            "<p>Really good choice in film.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #26
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Sunset Boulevard (1950). Arguably the greatest movie about Hollywood, Billy Wilder's masterpiece Sunset Boulevard is a tremendously entertaining combination of noir, black comedy, and character study.</p>
            <p><a href="https://www.youtube.com/watch?v=6j8JXbV7JWI" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>A tour de force for Swanson and one of Wilder's better efforts.</p>",
            "<p>One of Wilder's finest, and certainly the blackest of all Hollywood's scab-scratching accounts of itself.</p>",
            "<p>Still the best Hollywood movie ever made about Hollywood.</p>",
            "<p>This is the greatest film about Hollywood ever put on celluloid by Hollywood.</p>",
            "<p>Remains the best drama ever made about the movies because it sees through the illusions, even if Norma doesn't.</p>",
            "<p>While all the acting is memorable, one always thinks first and mostly of Miss Swanson, of her manifestation of consuming pride, her forlorn despair and a truly magnificent impersonation of Charlie Chaplin.</p>",
            "<p>Never heard of this one before. Interesting choice.</p>",
            "<p>Loved this movie.</p>",
        ]
        answer_index+=1

        #27
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>King Kong (1933). King Kong explores the soul of a monster -- making audiences scream and cry throughout the film -- in large part due to Kong's breakthrough special effects.</p>
            <p><a href="https://ianfarrington.files.wordpress.com/2016/07/kk1933.jpg" target="_blank">Classic scene</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>The story, like Frankenstein and Dracula, has taken on the significance of a modern folk tale, layered with obvious moralizing and as familiar as personal history.</p>",
            "<p>It might seem that any creature answering the description of Kong would be despicable and terrifying. Such is not the case. Kong is an exaggeration ad absurdum, too vast to be plausible. This makes his actions wholly enjoyable.</p>",
            "<p>Kong mystifies as well as it horrifies, and may open up a new medium for scaring babies via the screen.</p>",
            "<p>Through multiple exposures, processed 'shots' and a variety of angles of camera wizardry the producers set forth an adequate story and furnish enough thrills for any devotee of such tales.</p>",
            "<p>Even allowing for its slow start, wooden acting and wall-to-wall screaming, there is something ageless and primeval about King Kong that still somehow works.</p>",
            "<p>Willis O'Brien did the stop-action animation for this 1933 feature, which is richer in character than most of the human cast.</p>",
            "<p>Absolutely! how come I didn't think of this! One of the classics.</p>",
            "<p>Really good choice in film.</p>",
        ]
        answer_index+=1

        #28
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>The Adventures of Robin Hood (1938). Errol Flynn thrills as the legendary title character, and the film embodies the type of imaginative family adventure tailor-made for the silver screen.</p>
            <p><a href="https://s-media-cache-ak0.pinimg.com/originals/e6/9f/1d/e69f1dcf467960f9af7da6b9e66f52ce.jpg" target="_blank">https://s-media-cache-ak0.pinimg.com/originals/e6/9f/1d/e69f1dcf467960f9af7da6b9e66f52ce.jpg</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>If prankish Fairbanks was a man's Robin Hood, handsome, romantic Flynn performs for everybody else.</p>",
            "<p>It is cinematic pageantry at its best, a highly imaginative telling of folklore in all the hues of Technicolor.</p>",
            "<p>One of the few great adventure movies that you can pretend you are treating the kids to when you are really treating yourself.</p>",
            "<p>In these cynical days when swashbucklers cannot be presented without an ironic subtext, this great 1938 film exists in an eternal summer of bravery and romance.</p>",
            "<p>Sumptuous and highly energetic, The Adventures of Robin Hood is grand with a capital 'G' on every level.</p>",
            "<p>Few storybooks have been more brilliantly brought to life, page for page, chapter for chapter, derring-do for derring-do.</p>",
            "<p>Great choice in film</p>",
            "<p>A little dated for my tastes but still great.</p>"
        ]
        answer_index+=1

        #29
        answer = AnswerFactory(
            assignment=complex_assignment,
            user=students[answer_index],
            content="""
            <p>Seven Samurai (1956). Arguably Akira Kurosawa's masterpiece, The Seven Samurai is an epic adventure classic with an engrossing story, memorable characters, and stunning action sequences that make it one of the most influential films ever made.</p>
            <p><a href="https://www.youtube.com/watch?v=7mw6LyyoeGE" target="_blank">Trailer</a></p>
            """,
            draft=False,
            created=(now - datetime.timedelta(days=28) + datetime.timedelta(minutes=5*answer_index))
        )
        db.session.add(answer)
        db.session.commit()
        answer_comments[answer.id] = [
            "<p>The greatest movie ever made about warriors and battle.</p>",
            "<p>Kurosawa's film is a model of long-form construction, ably fitting its asides and anecdotes into a powerful suspense structure that endures for all of the film's 208 minutes.</p>",
            "<p>Besides the well-manned battlescenes, the pic has a good feeling for characterization and time</p>",
            "<p>[Kurosawa] has loaded his film with unusual and exciting physical incidents and made the whole thing graphic in a hard, realistic western style.</p>",
            "<p>Rich in detail, vivid in characterization, leisurely in exposition, this 207-minute epic is bravura filmmaking.</p>",
            "<p>Akira Kurosawa's The Seven Samurai (1954) is not only a great film in its own right, but the source of a genre that would flow through the rest of the century.</p>",
            "<p>Loved this movie.</p>",
            "<p>Great choice in film</p>",
        ]
        answer_index+=1

        #perform comparisons
        comparison_index = 0
        for rank_index, student in enumerate(students):
            for i in range(complex_assignment.number_of_comparisons):
                comparison = Comparison.create_new_comparison(complex_assignment.id, student.id, False)
                comparison.completed = True
                comparison.winner = WinningAnswer.answer1 if comparison.answer1_id < comparison.answer2_id else WinningAnswer.answer2
                comparison.created = (now - datetime.timedelta(days=20) + datetime.timedelta(minutes=5*comparison_index))
                for comparison_criterion in comparison.comparison_criteria:
                    comparison_criterion.winner = comparison.winner
                    comparison_criterion.created = (now - datetime.timedelta(days=20) + datetime.timedelta(minutes=5*comparison_index))
                db.session.add(comparison)

                Comparison.update_scores_1vs1(comparison)

                # add answer comment if necessary
                for answer in [comparison.answer1, comparison.answer2]:
                    answer_comment = AnswerComment.query \
                        .filter_by(
                            user_id=student.id,
                            answer_id=answer.id,
                            comment_type=AnswerCommentType.evaluation
                        ) \
                        .first()

                    if answer_comment == None:
                        content = answer_comments[answer.id].pop(0) if len(answer_comments[answer.id]) > 0 else ""
                        answer_comment = AnswerCommentFactory(
                            user=student,
                            answer=answer,
                            content=content,
                            comment_type=AnswerCommentType.evaluation,
                            created=(now - datetime.timedelta(days=20) + datetime.timedelta(minutes=5*comparison_index))
                        )
                        db.session.add(answer_comment)

                db.session.commit()
                comparison_index+=1

            answer = Answer.query \
                .filter_by(
                    assignment_id=complex_assignment.id,
                    user_id=student.id
                ) \
                .first()

            # self-evaluation
            answer_comment = AnswerCommentFactory(
                user=student,
                answer=answer,
                content="I think my overall rank in the class was around "+str(rank_index+1),
                comment_type=AnswerCommentType.self_evaluation,
                created=(now - datetime.timedelta(days=20) + datetime.timedelta(minutes=5*comparison_index))
            )
            db.session.commit()
            comparison_index+=1

        # calculate grades
        simple_assignment.calculate_grades()
        complex_assignment.calculate_grades()
        course.calculate_grades()
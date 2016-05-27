def register_api_blueprints(app):
    # Initialize rest of the api modules
    from .course import course_api
    app.register_blueprint(course_api, url_prefix='/api/courses')

    from .classlist import classlist_api
    app.register_blueprint(classlist_api, url_prefix='/api/courses/<int:course_id>/users')

    from .course_group import course_group_api
    app.register_blueprint(course_group_api, url_prefix='/api/courses/<int:course_id>/groups')

    from .course_group_user import course_group_user_api
    app.register_blueprint(course_group_user_api, url_prefix='/api/courses/<int:course_id>/users/<int:user_id>/groups')

    from .login import login_api
    app.register_blueprint(login_api)

    from .users import user_api
    app.register_blueprint(user_api, url_prefix='/api/users')

    from .system_role import system_roles_api
    app.register_blueprint(system_roles_api, url_prefix='/api/system_roles')

    from .course_role import user_course_role_api
    app.register_blueprint(user_course_role_api, url_prefix='/api/course_roles')

    from .assignment import assignment_api
    app.register_blueprint(assignment_api, url_prefix='/api/courses/<int:course_id>/assignments')

    from .answer import answers_api
    app.register_blueprint(
        answers_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>/answers')

    from .file import file_api
    app.register_blueprint(
        file_api,
        url_prefix='/api/attachment')

    from .assignment_comment import assignment_comment_api
    app.register_blueprint(
        assignment_comment_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>/comments')

    from .answer_comment import answer_comment_api
    app.register_blueprint(
        answer_comment_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>')

    from .criteria import criteria_api
    app.register_blueprint(criteria_api, url_prefix='/api/criteria')

    from .assignment_criteria import assignment_criteria_api
    app.register_blueprint(
        assignment_criteria_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>/criteria')

    from .comparison import comparison_api, all_course_comparisons_api
    app.register_blueprint(
        comparison_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>/comparisons')
    app.register_blueprint(
        all_course_comparisons_api,
        url_prefix='/api/courses/<int:course_id>/comparisons')

    from .report import report_api
    app.register_blueprint(report_api, url_prefix='/api/courses/<int:course_id>/report')

    from .gradebook import gradebook_api
    app.register_blueprint(
        gradebook_api,
        url_prefix='/api/courses/<int:course_id>/assignments/<int:assignment_id>/gradebook')

    from .common import timer_api
    app.register_blueprint(timer_api, url_prefix='/api/timer')

    @app.route('/')
    def route_root():
        return redirect('/static/index.html#/')

    return app


def log_events(log):
    # user events
    from .users import on_user_modified, on_user_get, on_user_list_get, on_user_create, on_user_course_get, \
        on_user_password_update, on_user_edit_button_get, on_teaching_course_get
    on_user_modified.connect(log)
    on_user_get.connect(log)
    on_user_list_get.connect(log)
    on_user_create.connect(log)
    on_user_course_get.connect(log)
    on_teaching_course_get.connect(log)
    on_user_edit_button_get.connect(log)
    on_user_password_update.connect(log)

    # system roles
    from .system_role import on_system_role_all_get
    on_system_role_all_get.connect(log)

    # course roles
    from .course_role import on_course_roles_all_get
    on_course_roles_all_get.connect(log)

    # course events
    from .course import on_course_modified, on_course_get, on_course_list_get, on_course_create, \
        on_user_course_answered_count
    on_course_modified.connect(log)
    on_course_get.connect(log)
    on_course_list_get.connect(log)
    on_course_create.connect(log)
    on_user_course_answered_count.connect(log)

    # assignment events
    from .assignment import on_assignment_modified, on_assignment_get, on_assignment_list_get, on_assignment_create, \
        on_assignment_delete
    on_assignment_modified.connect(log)
    on_assignment_get.connect(log)
    on_assignment_list_get.connect(log)
    on_assignment_create.connect(log)
    on_assignment_delete.connect(log)

    # assignment comment events
    from .assignment_comment import on_assignment_comment_modified, on_assignment_comment_get, \
        on_assignment_comment_list_get, on_assignment_comment_create, on_assignment_comment_delete
    on_assignment_comment_modified.connect(log)
    on_assignment_comment_get.connect(log)
    on_assignment_comment_list_get.connect(log)
    on_assignment_comment_create.connect(log)
    on_assignment_comment_delete.connect(log)

    # answer events
    from .answer import on_answer_modified, on_answer_get, on_answer_list_get, on_answer_create, on_answer_flag, \
        on_answer_delete, on_user_answer_get, on_user_answered_count
    on_answer_modified.connect(log)
    on_answer_get.connect(log)
    on_answer_list_get.connect(log)
    on_answer_create.connect(log)
    on_answer_flag.connect(log)
    on_answer_delete.connect(log)
    on_user_answer_get.connect(log)
    on_user_answered_count.connect(log)

    # answer comment events
    from .answer_comment import on_answer_comment_modified, on_answer_comment_get, on_answer_comment_list_get, \
        on_answer_comment_create, on_answer_comment_delete
    on_answer_comment_modified.connect(log)
    on_answer_comment_get.connect(log)
    on_answer_comment_list_get.connect(log)
    on_answer_comment_create.connect(log)
    on_answer_comment_delete.connect(log)

    # criteria events
    from .criteria import criteria_get, criteria_update, on_criteria_list_get, criteria_create
    criteria_get.connect(log)
    criteria_update.connect(log)
    on_criteria_list_get.connect(log)
    criteria_create.connect(log)

    # assignment criteria events
    from .assignment_criteria import on_assignment_criteria_create, on_assignment_criteria_delete, \
        on_assignment_criteria_get
    on_assignment_criteria_create.connect(log)
    on_assignment_criteria_delete.connect(log)
    on_assignment_criteria_get.connect(log)

    # comparison events
    from .comparison import on_comparison_get, on_comparison_create, on_comparison_update, \
        on_assignment_comparison_count, on_course_comparison_count
    on_comparison_get.connect(log)
    on_comparison_create.connect(log)
    on_comparison_update.connect(log)

    on_assignment_comparison_count.connect(log)
    on_course_comparison_count.connect(log)

    # classlist events
    from .classlist import on_classlist_get, on_classlist_upload, on_classlist_enrol, on_classlist_unenrol, \
        on_classlist_instructor_label, on_classlist_instructor, on_classlist_student
    on_classlist_get.connect(log)
    on_classlist_upload.connect(log)
    on_classlist_enrol.connect(log)
    on_classlist_unenrol.connect(log)
    on_classlist_instructor_label.connect(log)
    on_classlist_instructor.connect(log)
    on_classlist_student.connect(log)

    # course group events
    from .course_group import on_course_group_get, on_course_group_import, on_course_group_members_get
    on_course_group_get.connect(log)
    on_course_group_import.connect(log)
    on_course_group_members_get.connect(log)

    # course user group events
    from .course_group_user import on_course_group_user_create, on_course_group_user_delete
    on_course_group_user_create.connect(log)
    on_course_group_user_delete.connect(log)

    # report event
    from .report import on_export_report
    on_export_report.connect(log)

    # file attachment event
    from .file import on_save_tmp_file, on_file_get, on_file_delete
    on_save_tmp_file.connect(log)
    on_file_get.connect(log)
    on_file_delete.connect(log)

    # gradebook event
    from .gradebook import on_gradebook_get
    on_gradebook_get.connect(log)
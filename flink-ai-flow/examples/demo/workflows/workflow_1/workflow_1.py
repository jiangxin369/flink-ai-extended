import ai_flow as af
from ai_flow_plugins.job_plugins.bash import BashProcessor


def main():
    af.init_ai_flow_context()
    with af.job_config("task_1"):
        af.user_define_operation(processor=BashProcessor("echo hello"))

    workflow_name = af.current_workflow_config().workflow_name
    af.workflow_operation.submit_workflow(workflow_name)
    af.workflow_operation.start_new_workflow_execution(workflow_name)


if __name__ == '__main__':
    main()

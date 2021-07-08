from ai_flow_plugins.job_plugins.baichuan.baichuan_processor import BaichuanSensorProcessor

import ai_flow as af


def main():
    af.init_ai_flow_context()
    with af.job_config("task_1"):
        af.user_define_operation(processor=BaichuanSensorProcessor())

    workflow_name = af.current_workflow_config().workflow_name
    af.workflow_operation.submit_workflow(workflow_name)
    af.workflow_operation.start_new_workflow_execution(workflow_name)


if __name__ == '__main__':
    main()

package com.aiflow.entity;

import com.aiflow.proto.Message;
import com.aiflow.proto.MetadataServiceOuterClass;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class WorkflowMeta {
    private Long uuid;
    private String name;
    private Long project_id;
    private Map<String, String> properties;
    private Long create_time;
    private Long update_time;

    public WorkflowMeta() {}

    public WorkflowMeta(Long uuid, String name, Long project_id, Map<String, String> properties, Long create_time, Long update_time) {
        this.uuid = uuid;
        this.name = name;
        this.project_id = project_id;
        this.properties = properties;
        this.create_time = create_time;
        this.update_time = update_time;
    }

    public Long getUuid() {
        return uuid;
    }

    public void setUuid(Long uuid) {
        this.uuid = uuid;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Long getProject_id() {
        return project_id;
    }

    public void setProject_id(Long project_id) {
        this.project_id = project_id;
    }

    public Map<String, String> getProperties() {
        return properties;
    }

    public void setProperties(Map<String, String> properties) {
        this.properties = properties;
    }

    public Long getCreate_time() {
        return create_time;
    }

    public void setCreate_time(Long create_time) {
        this.create_time = create_time;
    }

    public Long getUpdate_time() {
        return update_time;
    }

    public void setUpdate_time(Long update_time) {
        this.update_time = update_time;
    }

    @Override
    public String toString() {
        return "WorkflowMeta{" +
                "uuid=" + uuid +
                ", name='" + name + '\'' +
                ", project_id=" + project_id +
                ", properties=" + properties +
                ", create_time=" + create_time +
                ", update_time=" + update_time +
                '}';
    }

    public static WorkflowMeta buildWorkflowMeta(Message.WorkflowMetaProto workflowMetaProto) {
        return workflowMetaProto == null ? null : new WorkflowMeta(workflowMetaProto.getUuid(),
                workflowMetaProto.getName(), workflowMetaProto.getProjectId().getValue(), workflowMetaProto.getPropertiesMap(),
                workflowMetaProto.getCreateTime().getValue(), workflowMetaProto.getUpdateTime().getValue());
    }

    public static List<WorkflowMeta> buildWorkflowMetas(MetadataServiceOuterClass.WorkflowListProto workflowListProto) {
        if (workflowListProto == null) {
            return null;
        } else {
            List<WorkflowMeta> workflowMetas = new ArrayList<>();
            for (Message.WorkflowMetaProto workflowMetaProto: workflowListProto.getWorkflowsList()) {
                workflowMetas.add(buildWorkflowMeta(workflowMetaProto));
            }
            return workflowMetas;
        }
    }
}
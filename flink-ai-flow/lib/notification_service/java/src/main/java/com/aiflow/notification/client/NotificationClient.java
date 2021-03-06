/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package com.aiflow.notification.client;

import com.aiflow.notification.entity.EventMeta;
import com.aiflow.notification.proto.NotificationServiceGrpc.NotificationServiceBlockingStub;
import com.aiflow.notification.proto.NotificationServiceOuterClass.*;
import com.google.common.util.concurrent.ThreadFactoryBuilder;
import io.grpc.ManagedChannelBuilder;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static com.aiflow.notification.entity.EventMeta.buildEventMeta;
import static com.aiflow.notification.proto.NotificationServiceGrpc.newBlockingStub;

public class NotificationClient {

    private static final Logger logger = LoggerFactory.getLogger(NotificationClient.class);
    private static final String SERVER_URI = "localhost:50051";
    private final String defaultNamespace;
    private final Integer listMemberIntervalMs;
    private final Integer retryIntervalMs;
    private final Integer retryTimeoutMs;
    private final Map<Map<String, String>, EventListener> threads;
    private final ExecutorService listMembersService;
    private NotificationServiceBlockingStub notificationServiceStub;
    private Set<MemberProto> livingMembers;
    private Boolean enableHa;
    private String currentUri;

    public NotificationClient(
            String target,
            String defaultNamespace,
            Boolean enableHa,
            Integer listMemberIntervalMs,
            Integer retryIntervalMs,
            Integer retryTimeoutMs) {
        this.defaultNamespace = defaultNamespace;
        this.enableHa = enableHa;
        this.listMemberIntervalMs = listMemberIntervalMs;
        this.retryIntervalMs = retryIntervalMs;
        this.retryTimeoutMs = retryTimeoutMs;
        if (enableHa) {
            String[] serverUris = StringUtils.split(target, ",");
            boolean lastError = true;
            for (String serverUri : serverUris) {
                currentUri = serverUri;
                try {
                    initNotificationServiceStub();
                    lastError = false;
                    break;
                } catch (Exception e) {
                    continue;
                }
            }
            if (lastError) {
                logger.warn("Failed to initialize client");
            }
        } else {
            currentUri = target;
            initNotificationServiceStub();
        }
        threads = new HashMap<>();
        livingMembers = new HashSet<>();
        listMembersService =
                Executors.newSingleThreadExecutor(
                        new ThreadFactoryBuilder()
                                .setDaemon(true)
                                .setNameFormat("list-members-%d")
                                .build());
        listMembersService.submit(listMembers());
    }

    /**
     * List specific registered listener events in Notification Service.
     *
     * @param serviceStub Notification service GRPC stub.
     * @param keys Keys of event for listening.
     * @param version (Optional) Version of event for listening.
     * @param timeoutSeconds List events request timeout seconds.
     * @return List of event updated in Notification Service.
     */
    protected static List<EventMeta> listEvents(
            NotificationServiceBlockingStub serviceStub,
            String namespace,
            List<String> keys,
            long version,
            String eventType,
            long startTime,
            Integer timeoutSeconds)
            throws Exception {
        ListEventsRequest request =
                ListEventsRequest.newBuilder()
                        .addAllKeys(keys)
                        .setStartVersion(version)
                        .setEventType(eventType)
                        .setStartTime(startTime)
                        .setNamespace(namespace)
                        .setTimeoutSeconds(timeoutSeconds)
                        .build();
        return parseEventsFromResponse(serviceStub.listEvents(request));
    }

    private static List<EventMeta> parseEventsFromResponse(ListEventsResponse response)
            throws Exception {
        if (response.getReturnCode() == ReturnStatus.SUCCESS) {
            List<EventMeta> eventMetas = new ArrayList<>();
            for (EventProto eventProto : response.getEventsList()) {
                eventMetas.add(buildEventMeta(eventProto));
            }
            return eventMetas;
        } else {
            throw new Exception(response.getReturnMsg());
        }
    }

    protected static NotificationServiceBlockingStub wrapBlockingStub(
            NotificationServiceBlockingStub stub,
            String target,
            Set<MemberProto> livingMembers,
            Boolean haRunning,
            Integer retryIntervalMs,
            Integer retryTimeoutMs) {
        return newBlockingStub(ManagedChannelBuilder.forTarget(target).usePlaintext().build())
                .withInterceptors(
                        new NotificationInterceptor(
                                stub,
                                target,
                                livingMembers,
                                haRunning,
                                retryIntervalMs,
                                retryTimeoutMs));
    }

    /** Initialize notification service stub. */
    protected void initNotificationServiceStub() {
        notificationServiceStub =
                newBlockingStub(
                        ManagedChannelBuilder.forTarget(
                                        StringUtils.isEmpty(currentUri) ? SERVER_URI : currentUri)
                                .usePlaintext()
                                .build());
        if (enableHa) {
            notificationServiceStub =
                    wrapBlockingStub(
                            notificationServiceStub,
                            StringUtils.isEmpty(currentUri) ? SERVER_URI : currentUri,
                            livingMembers,
                            enableHa,
                            retryIntervalMs,
                            retryTimeoutMs);
        }
    }

    /** Select a valid server from server candidates as current server. */
    protected void selectValidServer() {
        boolean lastError = false;
        for (MemberProto livingMember : livingMembers) {
            try {
                currentUri = livingMember.getServerUri();
                initNotificationServiceStub();
                ListMembersRequest request =
                        ListMembersRequest.newBuilder()
                                .setTimeoutSeconds(listMemberIntervalMs / 1000)
                                .build();
                ListMembersResponse response = notificationServiceStub.listMembers(request);
                if (response.getReturnCode() == ReturnStatus.SUCCESS) {
                    livingMembers = new HashSet<>(response.getMembersList());
                    lastError = false;
                    break;
                } else {
                    lastError = true;
                }
            } catch (Exception e) {
                lastError = true;
            }
        }
        if (lastError) {
            logger.warn("No available server uri!");
        }
    }

    /** List living members under high available mode. */
    protected Runnable listMembers() {
        return () -> {
            while (enableHa) {
                try {
                    if (Thread.currentThread().isInterrupted()) {
                        break;
                    }
                    ListMembersRequest request =
                            ListMembersRequest.newBuilder()
                                    .setTimeoutSeconds(listMemberIntervalMs / 1000)
                                    .build();
                    ListMembersResponse response = notificationServiceStub.listMembers(request);
                    if (response.getReturnCode() == ReturnStatus.SUCCESS) {
                        livingMembers = new HashSet<>(response.getMembersList());
                    } else {
                        logger.warn(response.getReturnMsg());
                        selectValidServer();
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                    logger.warn("Error while listening notification");
                    selectValidServer();
                }
            }
        };
    }

    /** Disable high availability mode. */
    public void disableHighAvailability() {
        enableHa = false;
        listMembersService.shutdown();
    }

    /**
     * Send the event to Notification Service.
     *
     * @param namespace Namespace of event updated in Notification Service.
     * @param key Key of event updated in Notification Service.
     * @param value Value of event updated in Notification Service.
     * @param eventType Type of event updated in Notification Service.
     * @param context Context of event updated in Notification Service.
     * @return Object of Event created in Notification Service.
     */
    public EventMeta sendEvent(
            String namespace, String key, String value, String eventType, String context)
            throws Exception {
        SendEventRequest request =
                SendEventRequest.newBuilder()
                        .setEvent(
                                EventProto.newBuilder()
                                        .setKey(key)
                                        .setValue(value)
                                        .setEventType(eventType)
                                        .setContext(context)
                                        .setNamespace(
                                                StringUtils.isEmpty(namespace)
                                                        ? defaultNamespace
                                                        : namespace)
                                        .build())
                        .setUuid(UUID.randomUUID().toString())
                        .build();
        SendEventsResponse response = notificationServiceStub.sendEvent(request);
        if (response.getReturnCode() == ReturnStatus.SUCCESS) {
            return buildEventMeta(response.getEvent());
        } else {
            throw new Exception(response.getReturnMsg());
        }
    }

    /**
     * List specific `key` or `version` notifications in Notification Service.
     *
     * @param namespace Namespace of notification for listening.
     * @param keys Keys of notification for listening.
     * @param version (Optional) Version of notification for listening.
     * @param eventType (Optional) Type of event for listening.
     * @param startTime (Optional) Type of event for listening.
     * @return List of Notification updated in Notification Service.
     */
    public List<EventMeta> listEvents(
            String namespace, List<String> keys, long version, String eventType, long startTime)
            throws Exception {
        return listEvents(
                notificationServiceStub,
                StringUtils.isEmpty(namespace) ? defaultNamespace : namespace,
                keys,
                version,
                eventType,
                startTime,
                0);
    }

    /**
     * List all registered listener events in Notification Service.
     *
     * @param startTime (Optional) The event create time after the given startTime.
     * @param startVersion (Optional) Start version of event for listening.
     * @param endVersion (Optional) End version of event for listening.
     * @return List of event updated in Notification Service.
     */
    public List<EventMeta> listAllEvents(long startTime, long startVersion, long endVersion)
            throws Exception {
        ListAllEventsRequest request =
                ListAllEventsRequest.newBuilder()
                        .setStartTime(startTime)
                        .setStartVersion(startVersion)
                        .setEndVersion(endVersion)
                        .build();
        ListEventsResponse response = notificationServiceStub.listAllEvents(request);
        return parseEventsFromResponse(response);
    }

    /**
     * Start listen specific `key` or `version` notifications in Notification Service.
     *
     * @param namespace Namespace of notification for listening.
     * @param key Key of notification for listening.
     * @param watcher Watcher instance for listening notification.
     * @param version (Optional) Version of notification for listening.
     * @param eventType (Optional) Type of event for listening.
     * @param startTime (Optional) Type of event for listening.
     */
    public void startListenEvent(
            String namespace,
            String key,
            EventWatcher watcher,
            long version,
            String eventType,
            long startTime) {
        Map<String, String> listenKey =
                new HashMap<String, String>() {
                    {
                        put(key, namespace);
                    }
                };
        if (!threads.containsKey(listenKey)) {
            ArrayList<String> curListenerKeys =
                    new ArrayList<String>() {
                        {
                            add(key);
                        }
                    };
            EventListener listener =
                    new EventListener(
                            notificationServiceStub,
                            curListenerKeys,
                            version,
                            eventType,
                            startTime,
                            StringUtils.isEmpty(namespace) ? defaultNamespace : namespace,
                            watcher,
                            5);
            listener.start();
            threads.put(listenKey, listener);
        }
    }

    /**
     * Stop listen specific `key` notifications in Notification Service.
     *
     * @param key Key of notification for listening.
     */
    public void stopListenEvent(String namespace, String key) {
        Map<String, String> listenKey =
                new HashMap<String, String>() {
                    {
                        put(key, StringUtils.isEmpty(namespace) ? defaultNamespace : namespace);
                    }
                };
        if (StringUtils.isEmpty(key)) {
            for (Map.Entry<Map<String, String>, EventListener> entry : threads.entrySet()) {
                entry.getValue().shutdown();
            }
        } else {
            if (threads.containsKey(listenKey)) {
                threads.get(listenKey).shutdown();
            }
        }
    }

    /**
     * Get latest version of specific `key` notifications in Notification Service.
     *
     * @param namespace Namespace of notification for listening.
     * @param key Key of notification for listening.
     */
    public long getLatestVersion(String namespace, String key) throws Exception {
        if (StringUtils.isEmpty(key)) {
            throw new Exception("Empty key, please provide valid key");
        } else {
            GetLatestVersionByKeyRequest request =
                    GetLatestVersionByKeyRequest.newBuilder()
                            .setNamespace(
                                    StringUtils.isEmpty(namespace) ? defaultNamespace : namespace)
                            .setKey(key)
                            .build();
            GetLatestVersionResponse response =
                    notificationServiceStub.getLatestVersionByKey(request);
            return parseLatestVersionFromResponse(response);
        }
    }

    public long parseLatestVersionFromResponse(GetLatestVersionResponse response) throws Exception {
        if (response.getReturnCode().equals(ReturnStatus.ERROR.toString())) {
            throw new Exception(response.getReturnMsg());
        } else {
            return response.getVersion();
        }
    }
}

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
package com.aiflow.common;

import com.aiflow.proto.Message.DataTypeProto;

public enum DataType {
    BIT(DataTypeProto.BIT),
    TINYINT(DataTypeProto.TINYINT),
    SMALLINT(DataTypeProto.SMALLINT),
    INTEGER(DataTypeProto.INTEGER),
    BIGINT(DataTypeProto.BIGINT),
    DECIMAL(DataTypeProto.DECIMAL),
    NUMERIC(DataTypeProto.NUMERIC),
    FLOAT(DataTypeProto.FLOAT),
    REAL(DataTypeProto.REAL),
    DATE(DataTypeProto.DATE),
    TIME(DataTypeProto.TIME),
    DATETIME(DataTypeProto.DATETIME),
    TIMESTAMP(DataTypeProto.TIMESTAMP),
    YEAR(DataTypeProto.YEAR),
    CHAR(DataTypeProto.CHAR),
    VARCHAR(DataTypeProto.VARCHAR),
    LONGVARCHAR(DataTypeProto.LONGVARCHAR),
    TEXT(DataTypeProto.TEXT),
    NCHAR(DataTypeProto.NCHAR),
    NVARCHAR(DataTypeProto.NVARCHAR),
    LONGNVARCHAR(DataTypeProto.LONGNVARCHAR),
    NTEXT(DataTypeProto.NTEXT),
    BINARY(DataTypeProto.BINARY),
    VARBINARY(DataTypeProto.VARBINARY),
    LONGVARBINARY(DataTypeProto.LONGVARBINARY),
    IMAGE(DataTypeProto.IMAGE),
    CLOB(DataTypeProto.CLOB),
    BLOB(DataTypeProto.BLOB),
    XML(DataTypeProto.XML),
    JSON(DataTypeProto.JSON);

    private DataTypeProto dataType;

    DataType(DataTypeProto dataType) {
        this.dataType = dataType;
    }

    public DataTypeProto getDataType() {
        return dataType;
    }
}
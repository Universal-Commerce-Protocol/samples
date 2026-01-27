/*
 * Copyright 2026 UCP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.dev.ucp.service.shopping.model;

import java.net.URI;
import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import org.springframework.lang.Nullable;
import com.fasterxml.jackson.databind.JsonNode;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * MessageInfo
 */

@JsonTypeName("Message_Info")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class MessageInfo implements Message {

  /**
   * Message type discriminator.
   */
  public enum TypeEnum {
    INFO("info");

    private final String value;

    TypeEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static TypeEnum fromValue(String value) {
      for (TypeEnum b : TypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private TypeEnum type;

  private @Nullable String path;

  private @Nullable String code;

  /**
   * Content format, default = plain.
   */
  public enum ContentTypeEnum {
    PLAIN("plain"),
    
    MARKDOWN("markdown");

    private final String value;

    ContentTypeEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static ContentTypeEnum fromValue(String value) {
      for (ContentTypeEnum b : ContentTypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private ContentTypeEnum contentType = ContentTypeEnum.PLAIN;

  private String content;

  public MessageInfo() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public MessageInfo(TypeEnum type, String content) {
    this.type = type;
    this.content = content;
  }

  public MessageInfo type(TypeEnum type) {
    this.type = type;
    return this;
  }

  /**
   * Message type discriminator.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Message type discriminator.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public TypeEnum getType() {
    return type;
  }

  public void setType(TypeEnum type) {
    this.type = type;
  }

  public MessageInfo path(@Nullable String path) {
    this.path = path;
    return this;
  }

  /**
   * RFC 9535 JSONPath to the component the message refers to.
   * @return path
   */
  
  @Schema(name = "path", description = "RFC 9535 JSONPath to the component the message refers to.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("path")
  public @Nullable String getPath() {
    return path;
  }

  public void setPath(@Nullable String path) {
    this.path = path;
  }

  public MessageInfo code(@Nullable String code) {
    this.code = code;
    return this;
  }

  /**
   * Info code for programmatic handling.
   * @return code
   */
  
  @Schema(name = "code", description = "Info code for programmatic handling.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("code")
  public @Nullable String getCode() {
    return code;
  }

  public void setCode(@Nullable String code) {
    this.code = code;
  }

  public MessageInfo contentType(ContentTypeEnum contentType) {
    this.contentType = contentType;
    return this;
  }

  /**
   * Content format, default = plain.
   * @return contentType
   */
  
  @Schema(name = "content_type", description = "Content format, default = plain.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("content_type")
  public ContentTypeEnum getContentType() {
    return contentType;
  }

  public void setContentType(ContentTypeEnum contentType) {
    this.contentType = contentType;
  }

  public MessageInfo content(String content) {
    this.content = content;
    return this;
  }

  /**
   * Human-readable message.
   * @return content
   */
  @NotNull 
  @Schema(name = "content", description = "Human-readable message.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("content")
  public String getContent() {
    return content;
  }

  public void setContent(String content) {
    this.content = content;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    MessageInfo messageInfo = (MessageInfo) o;
    return Objects.equals(this.type, messageInfo.type) &&
        Objects.equals(this.path, messageInfo.path) &&
        Objects.equals(this.code, messageInfo.code) &&
        Objects.equals(this.contentType, messageInfo.contentType) &&
        Objects.equals(this.content, messageInfo.content);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, path, code, contentType, content);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class MessageInfo {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    code: ").append(toIndentedString(code)).append("\n");
    sb.append("    contentType: ").append(toIndentedString(contentType)).append("\n");
    sb.append("    content: ").append(toIndentedString(content)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }
  
  public static class Builder {

    private MessageInfo instance;

    public Builder() {
      this(new MessageInfo());
    }

    protected Builder(MessageInfo instance) {
      this.instance = instance;
    }

    protected Builder copyOf(MessageInfo value) { 
      this.instance.setType(value.type);
      this.instance.setPath(value.path);
      this.instance.setCode(value.code);
      this.instance.setContentType(value.contentType);
      this.instance.setContent(value.content);
      return this;
    }

    public MessageInfo.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public MessageInfo.Builder path(String path) {
      this.instance.path(path);
      return this;
    }
    
    public MessageInfo.Builder code(String code) {
      this.instance.code(code);
      return this;
    }
    
    public MessageInfo.Builder contentType(ContentTypeEnum contentType) {
      this.instance.contentType(contentType);
      return this;
    }
    
    public MessageInfo.Builder content(String content) {
      this.instance.content(content);
      return this;
    }
    
    /**
    * returns a built MessageInfo instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public MessageInfo build() {
      try {
        return this.instance;
      } finally {
        // ensure that this.instance is not reused
        this.instance = null;
      }
    }

    @Override
    public String toString() {
      return getClass() + "=(" + instance + ")";
    }
  }

  /**
  * Create a builder with no initialized field (except for the default values).
  */
  public static MessageInfo.Builder builder() {
    return new MessageInfo.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public MessageInfo.Builder toBuilder() {
    MessageInfo.Builder builder = new MessageInfo.Builder();
    return builder.copyOf(this);
  }

}


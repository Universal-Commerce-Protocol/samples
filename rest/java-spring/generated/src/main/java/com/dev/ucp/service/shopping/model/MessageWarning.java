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
 * MessageWarning
 */

@JsonTypeName("Message_Warning")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class MessageWarning implements Message {

  /**
   * Message type discriminator.
   */
  public enum TypeEnum {
    WARNING("warning");

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

  private String code;

  private String content;

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

  public MessageWarning() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public MessageWarning(TypeEnum type, String code, String content) {
    this.type = type;
    this.code = code;
    this.content = content;
  }

  public MessageWarning type(TypeEnum type) {
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

  public MessageWarning path(@Nullable String path) {
    this.path = path;
    return this;
  }

  /**
   * JSONPath (RFC 9535) to related field (e.g., $.line_items[0]).
   * @return path
   */
  
  @Schema(name = "path", description = "JSONPath (RFC 9535) to related field (e.g., $.line_items[0]).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("path")
  public @Nullable String getPath() {
    return path;
  }

  public void setPath(@Nullable String path) {
    this.path = path;
  }

  public MessageWarning code(String code) {
    this.code = code;
    return this;
  }

  /**
   * Warning code. Machine-readable identifier for the warning type (e.g., final_sale, prop65, fulfillment_changed, age_restricted, etc.).
   * @return code
   */
  @NotNull 
  @Schema(name = "code", description = "Warning code. Machine-readable identifier for the warning type (e.g., final_sale, prop65, fulfillment_changed, age_restricted, etc.).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("code")
  public String getCode() {
    return code;
  }

  public void setCode(String code) {
    this.code = code;
  }

  public MessageWarning content(String content) {
    this.content = content;
    return this;
  }

  /**
   * Human-readable warning message that MUST be displayed.
   * @return content
   */
  @NotNull 
  @Schema(name = "content", description = "Human-readable warning message that MUST be displayed.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("content")
  public String getContent() {
    return content;
  }

  public void setContent(String content) {
    this.content = content;
  }

  public MessageWarning contentType(ContentTypeEnum contentType) {
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

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    MessageWarning messageWarning = (MessageWarning) o;
    return Objects.equals(this.type, messageWarning.type) &&
        Objects.equals(this.path, messageWarning.path) &&
        Objects.equals(this.code, messageWarning.code) &&
        Objects.equals(this.content, messageWarning.content) &&
        Objects.equals(this.contentType, messageWarning.contentType);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, path, code, content, contentType);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class MessageWarning {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    code: ").append(toIndentedString(code)).append("\n");
    sb.append("    content: ").append(toIndentedString(content)).append("\n");
    sb.append("    contentType: ").append(toIndentedString(contentType)).append("\n");
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

    private MessageWarning instance;

    public Builder() {
      this(new MessageWarning());
    }

    protected Builder(MessageWarning instance) {
      this.instance = instance;
    }

    protected Builder copyOf(MessageWarning value) { 
      this.instance.setType(value.type);
      this.instance.setPath(value.path);
      this.instance.setCode(value.code);
      this.instance.setContent(value.content);
      this.instance.setContentType(value.contentType);
      return this;
    }

    public MessageWarning.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public MessageWarning.Builder path(String path) {
      this.instance.path(path);
      return this;
    }
    
    public MessageWarning.Builder code(String code) {
      this.instance.code(code);
      return this;
    }
    
    public MessageWarning.Builder content(String content) {
      this.instance.content(content);
      return this;
    }
    
    public MessageWarning.Builder contentType(ContentTypeEnum contentType) {
      this.instance.contentType(contentType);
      return this;
    }
    
    /**
    * returns a built MessageWarning instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public MessageWarning build() {
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
  public static MessageWarning.Builder builder() {
    return new MessageWarning.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public MessageWarning.Builder toBuilder() {
    MessageWarning.Builder builder = new MessageWarning.Builder();
    return builder.copyOf(this);
  }

}


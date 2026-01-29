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
 * MessageError
 */

@JsonTypeName("Message_Error")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class MessageError implements Message {

  /**
   * Message type discriminator.
   */
  public enum TypeEnum {
    ERROR("error");

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

  private String code;

  private @Nullable String path;

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

  /**
   * Declares who resolves this error. 'recoverable': agent can fix via API. 'requires_buyer_input': merchant requires information their API doesn't support collecting programmatically (checkout incomplete). 'requires_buyer_review': buyer must authorize before order placement due to policy, regulatory, or entitlement rules (checkout complete). Errors with 'requires_*' severity contribute to 'status: requires_escalation'.
   */
  public enum SeverityEnum {
    RECOVERABLE("recoverable"),
    
    REQUIRES_BUYER_INPUT("requires_buyer_input"),
    
    REQUIRES_BUYER_REVIEW("requires_buyer_review");

    private final String value;

    SeverityEnum(String value) {
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
    public static SeverityEnum fromValue(String value) {
      for (SeverityEnum b : SeverityEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private SeverityEnum severity;

  public MessageError() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public MessageError(TypeEnum type, String code, String content, SeverityEnum severity) {
    this.type = type;
    this.code = code;
    this.content = content;
    this.severity = severity;
  }

  public MessageError type(TypeEnum type) {
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

  public MessageError code(String code) {
    this.code = code;
    return this;
  }

  /**
   * Error code. Possible values include: missing, invalid, out_of_stock, payment_declined, requires_sign_in, requires_3ds, requires_identity_linking. Freeform codes also allowed.
   * @return code
   */
  @NotNull 
  @Schema(name = "code", description = "Error code. Possible values include: missing, invalid, out_of_stock, payment_declined, requires_sign_in, requires_3ds, requires_identity_linking. Freeform codes also allowed.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("code")
  public String getCode() {
    return code;
  }

  public void setCode(String code) {
    this.code = code;
  }

  public MessageError path(@Nullable String path) {
    this.path = path;
    return this;
  }

  /**
   * RFC 9535 JSONPath to the component the message refers to (e.g., $.items[1]).
   * @return path
   */
  
  @Schema(name = "path", description = "RFC 9535 JSONPath to the component the message refers to (e.g., $.items[1]).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("path")
  public @Nullable String getPath() {
    return path;
  }

  public void setPath(@Nullable String path) {
    this.path = path;
  }

  public MessageError contentType(ContentTypeEnum contentType) {
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

  public MessageError content(String content) {
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

  public MessageError severity(SeverityEnum severity) {
    this.severity = severity;
    return this;
  }

  /**
   * Declares who resolves this error. 'recoverable': agent can fix via API. 'requires_buyer_input': merchant requires information their API doesn't support collecting programmatically (checkout incomplete). 'requires_buyer_review': buyer must authorize before order placement due to policy, regulatory, or entitlement rules (checkout complete). Errors with 'requires_*' severity contribute to 'status: requires_escalation'.
   * @return severity
   */
  @NotNull 
  @Schema(name = "severity", description = "Declares who resolves this error. 'recoverable': agent can fix via API. 'requires_buyer_input': merchant requires information their API doesn't support collecting programmatically (checkout incomplete). 'requires_buyer_review': buyer must authorize before order placement due to policy, regulatory, or entitlement rules (checkout complete). Errors with 'requires_*' severity contribute to 'status: requires_escalation'.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("severity")
  public SeverityEnum getSeverity() {
    return severity;
  }

  public void setSeverity(SeverityEnum severity) {
    this.severity = severity;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    MessageError messageError = (MessageError) o;
    return Objects.equals(this.type, messageError.type) &&
        Objects.equals(this.code, messageError.code) &&
        Objects.equals(this.path, messageError.path) &&
        Objects.equals(this.contentType, messageError.contentType) &&
        Objects.equals(this.content, messageError.content) &&
        Objects.equals(this.severity, messageError.severity);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, code, path, contentType, content, severity);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class MessageError {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    code: ").append(toIndentedString(code)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    contentType: ").append(toIndentedString(contentType)).append("\n");
    sb.append("    content: ").append(toIndentedString(content)).append("\n");
    sb.append("    severity: ").append(toIndentedString(severity)).append("\n");
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

    private MessageError instance;

    public Builder() {
      this(new MessageError());
    }

    protected Builder(MessageError instance) {
      this.instance = instance;
    }

    protected Builder copyOf(MessageError value) { 
      this.instance.setType(value.type);
      this.instance.setCode(value.code);
      this.instance.setPath(value.path);
      this.instance.setContentType(value.contentType);
      this.instance.setContent(value.content);
      this.instance.setSeverity(value.severity);
      return this;
    }

    public MessageError.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public MessageError.Builder code(String code) {
      this.instance.code(code);
      return this;
    }
    
    public MessageError.Builder path(String path) {
      this.instance.path(path);
      return this;
    }
    
    public MessageError.Builder contentType(ContentTypeEnum contentType) {
      this.instance.contentType(contentType);
      return this;
    }
    
    public MessageError.Builder content(String content) {
      this.instance.content(content);
      return this;
    }
    
    public MessageError.Builder severity(SeverityEnum severity) {
      this.instance.severity(severity);
      return this;
    }
    
    /**
    * returns a built MessageError instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public MessageError build() {
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
  public static MessageError.Builder builder() {
    return new MessageError.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public MessageError.Builder toBuilder() {
    MessageError.Builder builder = new MessageError.Builder();
    return builder.copyOf(this);
  }

}


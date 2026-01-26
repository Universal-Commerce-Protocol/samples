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

package com.dev.ucp.service;

import com.dev.ucp.service.shopping.CheckoutSessionsApiController;
import com.dev.ucp.service.shopping.model.Message;
import com.dev.ucp.service.shopping.model.MessageError;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * Centralized exception handling for UCP-compliant services.
 *
 * <p>This advice ensures that all exceptions thrown within the targeted controllers are surfaced as
 * structured UCP error responses. It automatically maps Java exceptions to protocol-standard error
 * codes and ensures the response body adheres to the UCP ErrorResponse schema.
 *
 * <p>Key features:
 *
 * <ul>
 *   <li><b>Dynamic Status Mapping:</b> Extracts HTTP status codes from {@link ResponseStatus}
 *       annotations on custom exceptions.
 *   <li><b>Standardized Error Codes:</b> Automatically converts exception class names to snake_case
 *       codes (e.g., PaymentFailedException -> payment_failed).
 *   <li><b>Escalation Signal:</b> Sets the checkout status to 'requires_escalation' to notify the
 *       platform that buyer intervention is needed.
 * </ul>
 *
 * <p>Reference: <a href="https://ucp.dev/specification/checkout-rest/#error-responses">UCP Checkout
 * REST - Error Responses</a>
 */
@ControllerAdvice(
    assignableTypes = {CheckoutSessionsApiController.class, DiscoveryController.class})
public class UCPExceptionControllerAdvice {

  private static final Logger logger = LoggerFactory.getLogger(UCPExceptionControllerAdvice.class);

  /** Simple record for UCP-compliant error responses. */
  public record ErrorResponse(String status, List<Message> messages) {}

  /**
   * Catches all unhandled exceptions and transforms them into structured UCP error responses.
   *
   * @param ex the exception to handle.
   * @return a {@link ResponseEntity} containing a UCP-compliant {@link ErrorResponse}.
   */
  @ExceptionHandler(Exception.class)
  public ResponseEntity<ErrorResponse> handleAllExceptions(Exception ex) {
    HttpStatus status = getResponseStatus(ex);
    String errorCode = convertToErrorCode(ex);

    if (status.is5xxServerError()) {
      logger.error("Internal Server Error: ", ex);
      return createErrorResponse(status, "internal_error", "An unexpected error occurred.");
    }

    logger.warn("{}: {}", ex.getClass().getSimpleName(), ex.getMessage());
    return createErrorResponse(status, errorCode, ex.getMessage());
  }

  /**
   * Specifically handles {@link IllegalArgumentException} resulting from validation or header
   * parsing errors.
   *
   * @param ex the exception to handle.
   * @return a {@link ResponseEntity} with {@code 400 Bad Request} and structured error details.
   */
  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<ErrorResponse> handleIllegalArgument(IllegalArgumentException ex) {
    logger.warn("Illegal argument: {}", ex.getMessage());
    return createErrorResponse(HttpStatus.BAD_REQUEST, "invalid_parameters", ex.getMessage());
  }

  /**
   * Handles {@link MethodArgumentNotValidException} which is thrown when {@code @Valid} validation
   * fails on a controller method argument.
   *
   * @param ex the exception to handle.
   * @return a {@link ResponseEntity} with {@code 400 Bad Request} and structured error details.
   */
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ErrorResponse> handleMethodArgumentNotValid(
      MethodArgumentNotValidException ex) {
    String message =
        ex.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));

    logger.warn("Validation failed: {}", message);
    return createErrorResponse(HttpStatus.BAD_REQUEST, "validation_failed", message);
  }

  private HttpStatus getResponseStatus(Exception ex) {
    ResponseStatus annotation =
        AnnotatedElementUtils.findMergedAnnotation(ex.getClass(), ResponseStatus.class);
    if (annotation != null) {
      return (HttpStatus) annotation.value();
    }
    return HttpStatus.INTERNAL_SERVER_ERROR;
  }

  private String convertToErrorCode(Exception ex) {
    String name = ex.getClass().getSimpleName();
    if (name.endsWith("Exception")) {
      name = name.substring(0, name.length() - "Exception".length());
    }
    // Convert CamelCase to snake_case
    return name.replaceAll("([a-z])([A-Z]+)", "$1_$2").toLowerCase();
  }

  private ResponseEntity<ErrorResponse> createErrorResponse(
      HttpStatus status, String code, String message) {
    MessageError error = new MessageError();
    error.setType(MessageError.TypeEnum.ERROR);
    error.setCode(code);
    error.setContent(message);
    error.setSeverity(MessageError.SeverityEnum.REQUIRES_BUYER_INPUT);

    ErrorResponse response = new ErrorResponse("requires_escalation", List.of(error));

    return new ResponseEntity<>(response, status);
  }
}

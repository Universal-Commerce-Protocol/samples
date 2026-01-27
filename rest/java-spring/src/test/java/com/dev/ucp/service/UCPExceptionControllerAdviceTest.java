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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.dev.ucp.exceptions.InvalidRequestException;
import com.dev.ucp.exceptions.ResourceNotFoundException;
import com.dev.ucp.service.shopping.model.MessageError;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public class UCPExceptionControllerAdviceTest {

  private final UCPExceptionControllerAdvice advice = new UCPExceptionControllerAdvice();

  @Test
  public void testHandleInvalidRequest() {
    InvalidRequestException ex = new InvalidRequestException("Invalid request message");
    ResponseEntity<UCPExceptionControllerAdvice.ErrorResponse> response =
        advice.handleAllExceptions(ex);

    assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
    assertNotNull(response.getBody());
    assertEquals("requires_escalation", response.getBody().status());

    MessageError error = (MessageError) response.getBody().messages().get(0);
    assertEquals("invalid_request", error.getCode());
    assertEquals("Invalid request message", error.getContent());
  }

  @Test
  public void testHandleResourceNotFound() {
    ResourceNotFoundException ex = new ResourceNotFoundException("Not found");
    ResponseEntity<UCPExceptionControllerAdvice.ErrorResponse> response =
        advice.handleAllExceptions(ex);

    assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    assertNotNull(response.getBody());

    MessageError error = (MessageError) response.getBody().messages().get(0);
    assertEquals("resource_not_found", error.getCode());
  }

  @Test
  public void testHandleIllegalArgument() {
    IllegalArgumentException ex = new IllegalArgumentException("Illegal arg");
    ResponseEntity<UCPExceptionControllerAdvice.ErrorResponse> response =
        advice.handleIllegalArgument(ex);

    assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
    assertNotNull(response.getBody());

    MessageError error = (MessageError) response.getBody().messages().get(0);
    assertEquals("invalid_parameters", error.getCode());
    assertEquals("Illegal arg", error.getContent());
  }

  @Test
  public void testHandleGeneralException() {
    Exception ex = new Exception("Internal");
    ResponseEntity<UCPExceptionControllerAdvice.ErrorResponse> response =
        advice.handleAllExceptions(ex);

    assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
    assertNotNull(response.getBody());

    MessageError error = (MessageError) response.getBody().messages().get(0);
    assertEquals("internal_error", error.getCode());
    assertEquals("An unexpected error occurred.", error.getContent());
  }
}

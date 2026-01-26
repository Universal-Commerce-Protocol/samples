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

package com.dev.ucp.exceptions;

import jakarta.validation.ConstraintViolation;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * Exception thrown when a UCP extension fails validation.
 *
 * <p>This exception results in an HTTP 400 Bad Request response.
 */
@ResponseStatus(value = HttpStatus.BAD_REQUEST)
public class ExtensionValidationException extends RuntimeException {
  private final Set<ConstraintViolation<?>> violations;

  public ExtensionValidationException(Set<ConstraintViolation<?>> violations) {
    super(formatMessage(violations));
    this.violations = violations;
  }

  public Set<ConstraintViolation<?>> getViolations() {
    return violations;
  }

  private static String formatMessage(Set<ConstraintViolation<?>> violations) {
    return violations.stream()
        .map(v -> v.getPropertyPath() + ": " + v.getMessage())
        .collect(Collectors.joining(", "));
  }
}

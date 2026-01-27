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

package com.dev.ucp;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingRequestWrapper;
import org.springframework.web.util.ContentCachingResponseWrapper;

/**
 * A debug filter that logs incoming HTTP requests and outgoing responses.
 *
 * <p>This class captures the request and response bodies (after they have been processed/converted
 * to JSON) and outputs them to the log, allowing developers to inspect the raw data being exchanged
 * with the server.
 */
@Component
public class HttpDebugLoggingFilter extends OncePerRequestFilter {

  private static final Logger logger = LoggerFactory.getLogger(HttpDebugLoggingFilter.class);

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {
    ContentCachingRequestWrapper requestWrapper = new ContentCachingRequestWrapper(request);
    ContentCachingResponseWrapper responseWrapper = new ContentCachingResponseWrapper(response);

    try {
      filterChain.doFilter(requestWrapper, responseWrapper);
    } finally {
      // Log after filter chain execution so wrappers are populated
      String requestBody = new String(requestWrapper.getContentAsByteArray());
      String responseBody = new String(responseWrapper.getContentAsByteArray());

      logger.debug("Request Endpoint: {}", requestWrapper.getRequestURI());
      StringBuilder requestHeaders = new StringBuilder();
      java.util.Collections.list(requestWrapper.getHeaderNames())
          .forEach(
              headerName ->
                  java.util.Collections.list(requestWrapper.getHeaders(headerName))
                      .forEach(
                          headerValue ->
                              requestHeaders
                                  .append(headerName)
                                  .append(": ")
                                  .append(headerValue)
                                  .append("\n")));
      if (requestHeaders.length() > 0) {
        logger.debug("Request Headers:\n{}", requestHeaders);
      }
      logger.debug("Request Body: {}", requestBody);

      StringBuilder responseHeaders = new StringBuilder();
      responseWrapper
          .getHeaderNames()
          .forEach(
              headerName ->
                  responseWrapper
                      .getHeaders(headerName)
                      .forEach(
                          headerValue ->
                              responseHeaders
                                  .append(headerName)
                                  .append(": ")
                                  .append(headerValue)
                                  .append("\n")));
      if (responseHeaders.length() > 0) {
        logger.debug("Response Headers:\n{}", responseHeaders);
      }
      logger.debug("Response Body: {}", responseBody);

      // IMPORTANT: Copy content back to original response
      responseWrapper.copyBodyToResponse();
    }
  }
}

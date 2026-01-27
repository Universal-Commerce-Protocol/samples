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

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestClient;

/** Main entry point for the Spring Demo application. */
@SpringBootApplication
@EnableAsync
@EnableJpaRepositories(considerNestedRepositories = true)
public class SpringDemoApp {

  public static void main(String[] args) {
    SpringApplication.run(SpringDemoApp.class, args);
  }

  @Bean
  public RestClient.Builder restClientBuilder() {
    return RestClient.builder().requestFactory(new SimpleClientHttpRequestFactory());
  }

}

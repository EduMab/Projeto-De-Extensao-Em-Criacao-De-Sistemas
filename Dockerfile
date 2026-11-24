FROM maven:3.9-eclipse-temurin-25 AS build

WORKDIR /build
COPY pom.xml .
COPY src ./src
COPY acervo ./acervo
COPY .docker-build-cache /root/.m2/repository
ARG MAVEN_BUILD_FLAGS=""
RUN mvn -B -ntp ${MAVEN_BUILD_FLAGS} clean package

FROM eclipse-temurin:25-jre

WORKDIR /app
COPY --from=build /build/target/*.jar /app/app.jar
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=65.0 -XX:+ExitOnOutOfMemoryError -Dfile.encoding=UTF-8"
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]

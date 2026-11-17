package com.kestrel.catalog.api;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.*;
import org.springframework.lang.NonNull;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

/** One place that turns failures into RFC 9457 problem details. */
@RestControllerAdvice
public class ApiErrors extends ResponseEntityExceptionHandler {

    public static class NotFound extends RuntimeException {
        public NotFound(String what) { super(what); }
    }

    public static class Conflict extends RuntimeException {
        public Conflict(String what) { super(what); }
    }

    public static class BadRequest extends RuntimeException {
        public BadRequest(String what) { super(what); }
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(@NonNull MethodArgumentNotValidException ex,
            @NonNull HttpHeaders headers, @NonNull HttpStatusCode status, @NonNull WebRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Request validation failed");
        pd.setTitle("Invalid request");
        pd.setType(URI.create("https://kestrel.example/problems/validation"));
        List<Map<String, String>> errors = new ArrayList<>();
        ex.getBindingResult().getFieldErrors().forEach(fe ->
                errors.add(Map.of("field", fe.getField().replaceAll("\\[\\d+].*$", ""),
                        "message", String.valueOf(fe.getDefaultMessage()))));
        ex.getBindingResult().getGlobalErrors().forEach(ge ->
                errors.add(Map.of("field", ge.getObjectName(), "message", String.valueOf(ge.getDefaultMessage()))));
        pd.setProperty("errors", errors);
        return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_PROBLEM_JSON).body(pd);
    }

    @ExceptionHandler(NotFound.class)
    ResponseEntity<ProblemDetail> notFound(NotFound ex) {
        return problem(HttpStatus.NOT_FOUND, "Not found", ex.getMessage());
    }

    @ExceptionHandler(Conflict.class)
    ResponseEntity<ProblemDetail> conflict(Conflict ex) {
        return problem(HttpStatus.CONFLICT, "Conflict", ex.getMessage());
    }

    @ExceptionHandler(BadRequest.class)
    ResponseEntity<ProblemDetail> badRequest(BadRequest ex) {
        return problem(HttpStatus.BAD_REQUEST, "Invalid request", ex.getMessage());
    }

    /** Backstop for races the pre-checks cannot see (two creates of the same slug at once). */
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<ProblemDetail> integrity(DataIntegrityViolationException ex) {
        return problem(HttpStatus.CONFLICT, "Conflict", "The request conflicts with existing data");
    }

    private ResponseEntity<ProblemDetail> problem(HttpStatus status, String title, String detail) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(title);
        return ResponseEntity.status(status).contentType(MediaType.APPLICATION_PROBLEM_JSON).body(pd);
    }
}

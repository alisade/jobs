package com.kestrel.catalog.api;

import jakarta.validation.Constraint;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import jakarta.validation.Payload;
import java.lang.annotation.*;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Cross-field rules: answerIndex points at an option, options are distinct (trimmed, case-insensitive). */
@Documented
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = ValidQuizItem.Validator.class)
public @interface ValidQuizItem {
    String message() default "invalid quiz item";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};

    class Validator implements ConstraintValidator<ValidQuizItem, Dtos.CreateQuizItem> {
        @Override
        public boolean isValid(Dtos.CreateQuizItem item, ConstraintValidatorContext ctx) {
            if (item == null || item.options() == null) return true; // @NotNull reports it
            boolean ok = true;
            ctx.disableDefaultConstraintViolation();
            Set<String> seen = new HashSet<>();
            for (String o : item.options()) {
                if (o != null && !seen.add(o.trim().toLowerCase(Locale.ROOT))) {
                    ctx.buildConstraintViolationWithTemplate("options must be distinct").addPropertyNode("options").addConstraintViolation();
                    ok = false;
                    break;
                }
            }
            Integer idx = item.answerIndex();
            if (idx != null && idx >= item.options().size()) {
                ctx.buildConstraintViolationWithTemplate("must point at one of the options").addPropertyNode("answerIndex").addConstraintViolation();
                ok = false;
            }
            return ok;
        }
    }
}

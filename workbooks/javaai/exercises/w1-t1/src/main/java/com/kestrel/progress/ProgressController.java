package com.kestrel.progress;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/learners")
public class ProgressController {
    private final ProgressService service;

    public ProgressController(ProgressService service) { this.service = service; }

    @GetMapping("/{learnerId}/progress")
    public ProgressView progress(@PathVariable String learnerId) {
        return service.progress(learnerId);
    }
}

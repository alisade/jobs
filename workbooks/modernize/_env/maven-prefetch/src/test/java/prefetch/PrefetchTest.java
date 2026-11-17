package prefetch;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** Running one test makes Maven download the surefire JUnit Platform provider too. */
class PrefetchTest {
    @Test
    void toolchainLoads() {
        assertTrue(Runtime.version().feature() >= 21);
    }
}

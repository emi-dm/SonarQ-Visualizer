<!-- Generated on 2026-02-12T14:28:29.849784 -->
<!-- Model: minimax/minimax-m2.1 -->
<!-- Sources: reports/security/issues_report_with_components.md, reports/maintainability/issues_report_with_components.md, reports/reliability/issues_report_with_components.md, reports/coverage/coverage_report.md -->

# Technology-Agnostic Common Errors Playbook

This playbook identifies recurring error patterns extracted from systematic code quality analysis. Each pattern includes detection signals, risk assessments, remediation strategies, and verification approaches applicable across technology stacks.

---

## 1. Untrusted Data in Output Streams

### Why It Happens

Developers frequently log user-provided input during debugging or monitoring without recognizing the security implications. This pattern emerges from several root causes: debugging artifacts left in production code, lack of awareness about log injection attacks, and absent sanitization layers between input handling and logging infrastructure. The pattern typically appears when developers need to trace request flow or validate user input processing.

### Risk Level

**Medium-High**

While not causing immediate runtime failures, untrusted data in output streams creates exploitation pathways for log injection attacks, enables information disclosure that aids reconnaissance, and may expose sensitive user information to unauthorized log access. The cumulative effect elevates this pattern's severity beyond its initial appearance.

### Detection Signals

Reviewers should examine any logging statements that incorporate data originating from external sources, including request parameters, user-provided payloads, header values, or query string data. Signal indicators include string concatenation or interpolation involving external variables, logging calls within request handlers without sanitization, and debug-level logging that might be enabled in production environments.

### Safe Rewrite Strategy

Separate the logging of operational metadata from user content. Establish a logging filter or sanitization layer that redacts or removes user-controlled data before emission. If correlation is required, use synthetic identifiers rather than raw user input. Structure logging formats to limit what content can be embedded, preventing injection of control characters or escape sequences.

### Verification Checks

Confirm that logging statements contain only application-generated metadata. Verify that any user identifiers referenced in logs are synthetic or hashed rather than raw input values. Test logging behavior with malicious input containing newline characters, escape sequences, and unusually long strings to confirm proper handling.

---

## 2. Obsolete Language Feature Usage

### Why It Happens

Codebases accumulate technical debt when developers continue using patterns that predate newer language features. This occurs in several scenarios: projects established before feature availability, copy-paste from older codebases, and incomplete migration during language version upgrades. The pattern often concentrates in specific architectural layers where certain coding patterns were historically required.

### Risk Level

**Medium**

Obsolete patterns rarely cause runtime failures but compound over time. They increase maintenance burden, reduce IDE support effectiveness, complicate documentation generation, and create friction during team onboarding. The accumulation of such patterns signals deeper technical debt that may eventually impact development velocity.

### Detection Signals

Identify code patterns that predate language versions currently in active use. Common signals include dependency declarations without modern type annotation wrappers, manual workarounds for features now built into standard libraries, and configuration patterns replaced by newer declarative approaches. The pattern typically appears consistently across multiple files in the same architectural layer.

### Safe Rewrite Strategy

Research the current recommended patterns for dependency declaration and type annotation in your language. Systematically update affected declarations to leverage modern equivalents, ensuring consistency across all instances. Verify that type checking and IDE support improve after the migration.

### Verification Checks

Confirm that all affected patterns have been updated to current standards. Validate that type checking passes without warnings. Ensure that runtime behavior remains identical after refactoring.

---

## 3. Inverted Conditional Logic

### Why It Happens

Developers sometimes write conditions that check for negative states as the primary branch, leaving positive cases in else blocks. This pattern emerges when handling edge cases first, when original logic was inverted during debugging and never corrected, or when requirements shifted but conditional structure was not revisited. Negated conditions require additional cognitive effort to parse during code review.

### Risk Level

**Low-Medium**

Inverted conditions function correctly but impair readability and increase maintenance cost. The risk compounds when conditions are nested or combined with boolean operators, creating opportunities for logical errors during future modifications.

### Detection Signals

Reviewers should flag conditional statements where the primary branch handles the negative case through negation operators, particularly when the else branch contains simpler logic. Pay attention to conditions using operators like "not equal," "not in," or explicit negation on compound expressions.

### Safe Rewrite Strategy

Invert the condition and swap the branch contents so that the positive case executes first. Rename the condition to express what is being checked for rather than what is being avoided. This refactoring typically places the common path in the primary branch and edge cases in secondary branches.

### Verification Checks

Confirm that all test cases pass after refactoring. Verify that the logical behavior is identical by tracing through each possible input path. Ensure that the updated condition name accurately describes the positive case being tested.

---

## 4. Excessive Cognitive Complexity

### Why It Happens

Functions grow excessively complex when multiple concerns are intermixed without extraction, when business rules require numerous conditional branches, and when developers repeatedly extend existing functions rather than refactoring. Complexity often accumulates incrementally during feature development, with each addition seeming justifiable in isolation.

### Risk Level

**Medium-High**

Functions exceeding complexity thresholds correlate strongly with defect density and maintenance difficulty. Such functions are difficult to test comprehensively, prone to edge case oversights, and create elevated risk during any modification. The testing and review effort required grows non-linearly with complexity.

### Detection Signals

Reviewers should identify functions with deep nesting across multiple levels, functions containing numerous conditional branches, and functions exceeding a defined complexity threshold established by team standards. Particular attention should go to functions handling multiple business rules or validation steps within a single unit.

### Safe Rewrite Strategy

Decompose complex functions into smaller units, each addressing a single concern. Extract conditional branches into named helper functions with descriptive names. Apply early return patterns to reduce nesting depth. Replace complex boolean expressions with named predicates that document their purpose.

### Verification Checks

Confirm that extracted functions maintain identical behavior through comprehensive test coverage. Verify that the original function's complexity score decreases below the threshold. Ensure that all execution paths remain testable and are exercised by existing or new tests.

---

## 5. Empty or Meaningless Exception Handlers

### Why It Happens

Exception handlers are sometimes added defensively without implementing appropriate response logic. This pattern occurs when developers catch exceptions to prevent failures but lack clarity on appropriate recovery, when exceptions are caught at layers that cannot meaningfully respond, and when error handling is considered lower priority than feature implementation.

### Risk Level

**Medium-High**

Empty or ineffective exception handlers mask errors, complicate debugging, and create inconsistent system state. Errors that should propagate are suppressed, leading to failures that appear without context in distant system layers.

### Detection Signals

Reviewers should examine exception handlers that catch exceptions without meaningful action, handlers where caught variables are unused, and cases where exceptions are caught and logged at inappropriate abstraction levels. Pay attention to handlers that catch broad exception types without specific recovery logic.

### Safe Rewrite Strategy

Implement exception handlers that either perform meaningful recovery appropriate to the abstraction level, add contextual information through structured logging before re-raising, or remove the handler entirely and allow exceptions to propagate to callers that can respond appropriately.

### Verification Checks

Confirm that exceptions are either handled with appropriate recovery or propagated with adequate context. Verify that error scenarios are covered by tests that confirm expected behavior. Ensure that logging statements capture sufficient context for debugging without exposing sensitive information.

---

## 6. Time Handling Without Timezone Semantics

### Why It Happens

Developers frequently create timestamps using methods that return naive datetime objects without timezone information. This pattern is especially prevalent in test code where deterministic timing is needed. The pattern persists because naive timestamps often work in isolated testing environments, with timezone bugs emerging only during production use or when comparing timestamps from different sources.

### Risk Level

**High**

Time handling without timezone semantics causes reliability issues that may only manifest under specific conditions, making them difficult to detect and diagnose. Test flakiness, incorrect time comparisons, and incorrect ordering of events all stem from this pattern.

### Detection Signals

Reviewers should identify creation of timestamps without timezone information, comparisons between timezone-aware and timezone-naive timestamps, and serialization of naive timestamps for storage or transmission. The pattern appears frequently in test code creating expected timestamps for assertion.

### Safe Rewrite Strategy

Always create timestamps with explicit timezone information, typically using UTC. For test scenarios requiring deterministic timestamps, use fixtures or libraries that provide controlled time manipulation rather than relying on system clock values. Centralize timestamp creation in shared utilities to ensure consistency.

### Verification Checks

Confirm that all timestamp creation includes timezone specification. Verify that comparisons are only made between timestamps with matching timezone semantics. Ensure that test suites produce consistent results across multiple runs.

---

## 7. Floating Point Equality Assertions

### Why It Happens

Developers write assertions comparing floating point values using direct equality operators, not recognizing that arithmetic operations may produce values that differ by minute rounding errors. This pattern commonly appears in test code validating calculated results, where expected values are computed differently from implementation logic.

### Risk Level

**Medium**

Floating point equality comparisons cause test failures that are false negatives—the tests fail despite correct implementation behavior. This pattern wastes investigation time and can lead developers to incorrectly modify correct code.

### Detection Signals

Reviewers should identify assertions using equality operators on floating point values, particularly in test code validating mathematical calculations or aggregated values. Pay attention to comparisons involving division, multiplication, or accumulated floating point operations.

### Safe Rewrite Strategy

Replace direct equality comparisons with approximate equality checks that allow for a defined tolerance. The tolerance should reflect the precision requirements of the domain while accounting for expected rounding behavior. Document the chosen tolerance and its rationale.

### Verification Checks

Confirm that assertions using approximate equality pass with values within the defined tolerance. Verify that values significantly outside the tolerance still trigger failures. Ensure that the tolerance is calibrated to the precision requirements of the domain.

---

## 8. Misuse of Data Serialization Parameters

### Why It Happens

HTTP client APIs often provide multiple parameters for request bodies, each with distinct semantics. Developers sometimes use parameters intended for different content types or encoding approaches, resulting in incorrectly formatted requests. This pattern emerges when developers copy request construction patterns without understanding parameter differences or when APIs have evolved and documentation is outdated.

### Risk Level

**Medium-High**

Incorrect request body formatting causes API errors that may be masked during testing if servers perform implicit conversion. The bug manifests as failures in production or when server implementations change.

### Detection Signals

Reviewers should examine HTTP request construction, particularly POST and PUT operations, for correct specification of content type parameters. Pay attention to cases where string data is passed to parameters intended for form-encoded or binary data.

### Safe Rewrite Strategy

Use parameters explicitly designed for the content type being sent. For JSON bodies, use the dedicated JSON parameter. For form-encoded data, use the form data parameter. Verify that the server receives content in the expected format by examining raw request bodies during testing.

### Verification Checks

Confirm that request construction uses parameters matching the intended content type. Verify that server-side parsing receives data in the expected format. Ensure that integration tests validate request formatting.

---

## 9. Incorrect Global Function Usage

### Why It Happens

Legacy JavaScript global functions are sometimes used without recognizing that their type coercion behavior differs from stricter modern alternatives. This pattern persists through copy-paste from older examples, incomplete migration to modern patterns, and lack of awareness about the distinction between global and number-method functions.

### Risk Level

**Low**

Incorrect NaN checking rarely causes runtime errors but may lead to incorrect branch execution in edge cases. The pattern functions incorrectly but may not be triggered by typical input values.

### Detection Signals

Reviewers should identify usage of global type-checking functions that perform type coercion. Pay particular attention to checks on user input or data from external sources where coercion behavior may produce unexpected results.

### Safe Rewrite Strategy

Replace global type-checking functions with their stricter method-based equivalents that do not perform type coercion. These methods only return true for the specific case being checked without attempting type conversion.

### Verification Checks

Confirm that type checks correctly identify the specific case they target. Verify that edge cases involving type coercion no longer produce incorrect results. Ensure that linting rules prevent future usage of the non-strict alternatives.

---

## 10. Insufficient Test Coverage

### Why It Happens

Test coverage gaps accumulate when new code is written without corresponding tests, when refactoring leaves tests behind, and when test suites focus on easy-to-test happy paths rather than comprehensive coverage. Coverage metrics below established thresholds indicate that portions of the codebase are untested, creating risk that defects in those areas will not be caught before production deployment.

### Risk Level

**High**

Untested code paths contain undetected defects that will manifest in production. The absence of tests also means defects introduced during future modifications will not be caught by existing test suites.

### Detection Signals

Reviewers should examine coverage reports to identify files and functions with low or no coverage. Pay particular attention to files handling critical functionality, data validation, or external integrations. Identify branches and conditions that lack test coverage.

### Safe Rewrite Strategy

Prioritize test coverage for critical paths, complex logic, and areas with historical defects. Write tests that exercise uncovered branches and edge cases. Use coverage analysis to identify untested code paths and systematically add coverage.

### Verification Checks

Confirm that coverage metrics meet established thresholds. Verify that critical functionality is exercised by multiple test cases. Ensure that new code includes corresponding tests before merge.

---

## Prevention Guardrails

These guardrails represent preventive measures that development teams should implement before writing code. Applying these measures systematically reduces the introduction of common error patterns.

### Input Validation and Sanitization

Establish clear separation between raw external input and any output streams including logs, error messages, and user-facing content. All external data must pass through validation and sanitization layers before use. Define clear policies on what data categories may appear in each output context.

### Modern Pattern Adoption

Before starting new work, verify that your development environment and tooling support current language versions. Research and adopt recommended patterns for common operations including dependency declaration, time handling, and type annotations. Avoid copying patterns from older codebases without verification.

### Complexity Management

Enforce complexity thresholds through static analysis tooling. Break down functions that approach complexity limits before they exceed thresholds. Use named functions and early returns to flatten conditional logic. Treat complexity accumulation as technical debt requiring immediate attention.

### Error Handling Standards

Define clear policies on exception handling at each architectural layer. Establish conventions for when exceptions should propagate versus when they should be handled locally. Ensure that all exception handlers either perform meaningful recovery or add context before re-raising.

### Testing Infrastructure

Implement coverage reporting as part of the continuous integration pipeline. Set quality gates that prevent merges degrading coverage below established thresholds. Integrate static analysis for common patterns into pre-commit validation.

---

## Pre-commit Quality Checklist

Complete these checks before committing code changes. Each item represents a verification step that catches common errors before they enter the codebase.

### Security Verification

- [ ] No logging statements contain variables originating from external input
- [ ] No sensitive data categories appear in any output statements
- [ ] All external data passes through appropriate validation before use
- [ ] Authentication and authorization checks are present on all protected operations

### Pattern Verification

- [ ] No deprecated language features or patterns are used for common operations
- [ ] Conditional logic expresses positive cases in primary branches
- [ ] Exception handlers perform meaningful actions or propagate appropriately
- [ ] No hardcoded credentials, keys, or sensitive configuration values are present

### Test Coverage Verification

- [ ] New code includes corresponding tests exercising normal and edge cases
- [ ] Modified code has updated tests maintaining coverage levels
- [ ] Critical paths are exercised by multiple test scenarios
- [ ] Integration tests validate interactions between components

### Complexity Verification

- [ ] No function exceeds established complexity thresholds
- [ ] Complex conditional logic is extracted into named helper functions
- [ ] Deeply nested code has been flattened through early returns or extraction
- [ ] Boolean expressions use named predicates where logic is non-trivial

### Data Handling Verification

- [ ] All timestamp creation includes explicit timezone specification
- [ ] Floating point comparisons use appropriate tolerance-based assertions
- [ ] HTTP request construction uses correct parameters for content types
- [ ] Type-checking functions use non-coercing alternatives where available

---

## Coverage Reliability Rules

These rules connect test coverage metrics to defect prevention strategies. Each rule establishes a coverage expectation correlated with reduced defect rates.

### Branch Coverage Threshold

Functions with branch coverage below 70% correlate with elevated defect density. Target minimum 70% branch coverage on all files containing business logic. Files below this threshold should be prioritized for test addition.

### Critical Path Coverage

Critical paths—sequences of operations that, if defective, would cause data corruption, security breach, or system failure—require minimum 95% coverage. Critical path coverage should be verified through integration tests that exercise complete workflows.

### Edge Case Coverage

Test suites should explicitly address boundary conditions for all numeric inputs, string length limits, null and empty states, and type variations. Evidence of edge case testing should appear in code review for all logic handling external input.

### Defect-driven Coverage

When a defect escapes to production, the corresponding fix must include a test that would have caught the defect. This regression test ensures that previously fixed defects remain fixed and prevents recurrence of similar issues.

### Coverage Trend Monitoring

Monitor coverage trends over time rather than focusing solely on absolute values. Coverage declining from previous baselines indicates accumulation of technical debt. Establish processes to investigate and address coverage degradation.

### Complexity-coverage Correlation

Functions with high complexity should have proportionally higher coverage expectations. A function with complexity approaching thresholds should have near-complete coverage to ensure that complex logic is thoroughly validated.

---

## Pattern Summary Reference

| Pattern | Risk Level | Primary Detection Signal | Key Prevention |
|---------|------------|--------------------------|----------------|
| Untrusted Data in Output | Medium-High | External data in logging statements | Sanitization layers |
| Obsolete Language Features | Medium | Patterns predating current language version | Pattern migration |
| Inverted Conditionals | Low-Medium | Negative case in primary branch | Condition refactoring |
| Excessive Complexity | Medium-High | Functions exceeding threshold | Decomposition |
| Empty Exception Handlers | Medium-High | Unused exception variables | Recovery or propagation |
| Naive Time Handling | High | Timestamps without timezone | Timezone-aware creation |
| Float Equality | Medium | Equality on floating point values | Tolerance-based comparison |
| Serialization Misuse | Medium-High | Incorrect HTTP body parameters | Content-type verification |
| Incorrect Global Usage | Low | Coercing type-check functions | Non-coercing alternatives |
| Insufficient Coverage | High | Coverage below thresholds | Test addition |

---

*This playbook should be reviewed and updated as new patterns emerge from ongoing code quality analysis.*
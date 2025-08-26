---
inclusion: always
---

# Development Guidelines & Code Protection Rules

## Code Modification Protocol

### Before Making Changes
- **Analyze first**: Always examine existing code for similar functionality
- **Explain rationale**: Document why changes are necessary and their scope
- **Seek approval**: Request explicit user permission before modifying existing code
- **Preserve patterns**: Maintain established coding conventions and architecture

### Implementation Approach
- **Reuse over rewrite**: Extend existing functions rather than creating duplicates
- **Minimal impact**: Make the smallest change necessary to achieve the goal
- **Consistency**: Follow existing naming conventions and code structure
- **Incremental**: Build upon existing functionality when possible

## Code Quality Standards

### Development Principles
- **Senior-level practices**: Apply enterprise-grade development standards
- **Maintainability**: Write code that is easy to understand and modify
- **Modularity**: Create independent, testable functions with clear responsibilities
- **Loose coupling**: Minimize dependencies between components

### Coding Standards
- **Function design**: Each function should have a single, clear purpose
- **Naming consistency**: Follow existing variable and function naming patterns
- **Reusability**: Design components for multiple use cases
- **Documentation**: Include Korean comments explaining complex logic
- **Error handling**: Implement proper exception handling and logging

## Task Development Requirements

### Task Structure
- **Atomic delivery**: Each task must produce complete, working functionality
- **Independent testing**: Tasks should be verifiable in isolation
- **Incremental progress**: Build working features step by step
- **Clear acceptance criteria**: Define measurable success conditions

### Quality Gates
Before completing any task, ensure:
- [ ] Existing codebase analyzed for reusable components
- [ ] Code follows established patterns and conventions
- [ ] Functions are modular and testable
- [ ] Dependencies are minimized
- [ ] User approval obtained for any modifications
- [ ] Korean documentation added where appropriate
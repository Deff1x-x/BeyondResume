# BeyondResume Design System v1.0

> Single Source of Truth for every visual, UX and frontend decision.

------------------------------------------------------------------------

# 1. Mission

BeyondResume is a premium career platform.

Artificial Intelligence is an implementation detail, not the product
identity.

The interface must communicate:

-   professionalism
-   trust
-   clarity
-   confidence
-   precision

Never "AI magic".

------------------------------------------------------------------------

# 2. Core Principles

1.  Professional over flashy.
2.  Clarity over decoration.
3.  Consistency over novelty.
4.  Accessibility before aesthetics.
5.  Reusable components only.
6.  One design language across the product.
7.  White space is part of the design.
8.  Motion supports understanding.
9.  Data is the hero.
10. AI stays in the background.

------------------------------------------------------------------------

# 3. Brand Personality

Professional. Calm. Premium. Trustworthy. Modern. Human.

Avoid words like: - revolutionary - magical - unbelievable - powered by
AI

Prefer: - verified - analyzed - matched - recommended - evidence -
insights

------------------------------------------------------------------------

# 4. Anti‑Patterns

Never use:

-   purple AI gradients
-   glowing borders
-   glassmorphism as primary style
-   robots
-   brain illustrations
-   neural network graphics
-   crypto aesthetics
-   unnecessary animations

------------------------------------------------------------------------

# 5. Typography

Primary font: Inter

Fallback: system-ui

Use tabular numbers.

Hierarchy:

H1 H2 H3 Body L Body Small Caption

Readable line length: 60--80 characters.

------------------------------------------------------------------------

# 6. Color System

Primary: #2563EB

Accent: #0891B2

Success: #16A34A

Warning: #D97706

Danger: #DC2626

Background: #FAFBFC

Surface: #FFFFFF

Border: #E5E7EB

Text: #111827

Secondary: #4B5563

Muted: #9CA3AF

No gradients by default.

------------------------------------------------------------------------

# 7. Spacing

8pt grid only.

Allowed spacing:

4 8 12 16 24 32 40 48 64 96

------------------------------------------------------------------------

# 8. Radius

Buttons: 12px

Inputs: 12px

Cards: 16px

Dialogs: 20px

Never mix random radii.

------------------------------------------------------------------------

# 9. Shadows

Soft elevation only.

Never create floating cards everywhere.

------------------------------------------------------------------------

# 10. Icons

Lucide Icons only.

Do not mix icon libraries.

------------------------------------------------------------------------

# 11. Layout

Desktop-first.

Primary: 1440px

Supported: 1920px

Minimum: 1280px

Mobile is outside MVP.

------------------------------------------------------------------------

# 12. Navigation

Left sidebar.

Top workspace header.

Content center.

Optional right insight panel.

------------------------------------------------------------------------

# 13. Components

Canonical components:

-   Button
-   IconButton
-   Input
-   Textarea
-   Select
-   Checkbox
-   Radio
-   Switch
-   Badge
-   Avatar
-   Card
-   Table
-   Tabs
-   Modal
-   Drawer
-   Tooltip
-   Toast
-   Progress
-   Skeleton
-   Empty State
-   File Upload

No duplicate implementations.

------------------------------------------------------------------------

# 14. Forms

Labels always visible.

Errors below fields.

44px minimum input height.

Required fields clearly marked.

------------------------------------------------------------------------

# 15. Tables

Sticky header.

Hover state.

Sorting.

Filtering.

Dense but readable.

------------------------------------------------------------------------

# 16. Dashboard

Dashboard is a workspace.

Do not imitate CRM dashboards.

Focus on decisions.

------------------------------------------------------------------------

# 17. Resume UX

Upload must feel safe.

Always show:

-   validation
-   upload progress
-   parsing status
-   completion state

Never expose internal backend concepts.

------------------------------------------------------------------------

# 18. Loading

Prefer Skeleton.

Avoid infinite spinners.

------------------------------------------------------------------------

# 19. Empty States

Every empty state explains:

-   why
-   what to do next

------------------------------------------------------------------------

# 20. Error Handling

Errors are calm.

Explain the problem.

Offer next action.

Never blame the user.

------------------------------------------------------------------------

# 21. Motion

Hover: 120ms

Dropdown: 160ms

Modal: 200ms

Toast: 180ms

Animations must improve understanding.

------------------------------------------------------------------------

# 22. Accessibility

Keyboard support.

Visible focus.

Semantic HTML.

Good contrast.

ARIA where needed.

------------------------------------------------------------------------

# 23. Content

Tone:

Professional.

Helpful.

Concise.

Avoid marketing language.

------------------------------------------------------------------------

# 24. AI Principles

AI is never the visual hero.

Users should discover AI naturally through useful features.

Do not decorate pages with AI imagery.

------------------------------------------------------------------------

# 25. Future

Dark mode planned.

Employer workspace.

GitHub Passport.

Analytics.

Mobile.

All future work must extend---not replace---this design language.

------------------------------------------------------------------------

# 26. Design Review Checklist

Before any UI merge verify:

-   Matches design tokens
-   Uses existing components
-   Correct spacing
-   Correct typography
-   Accessible
-   Responsive for supported widths
-   Proper loading state
-   Proper error state
-   Proper empty state
-   No visual regressions

------------------------------------------------------------------------

# 27. Rules for Cursor / AI Developers

Cursor must not:

-   invent colors
-   invent spacing
-   invent typography
-   invent components
-   invent animations

If a design decision is missing:

1.  Update this document.
2.  Review.
3.  Only then implement.

This document is the authoritative source for all frontend visual
decisions.

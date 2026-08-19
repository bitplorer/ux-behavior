# Pattern catalog (coverage map)

## Widgets

Tabs · Toasts · Dropdown · Modal · Carousel · Accordion · Drawer · Wizard · Pagination · Filters · Typeahead · Confirm · Forms

## Complex

Endless scroll · Virtual list · Optimistic UI · Debounced search · Faceted+URL · Data table bulk · Master/detail · Notifications · Social feed · Chat · Kanban · Calendar · Upload · Command palette · Mega menu · Consent · Onboarding · Banner · Compare · Saved views · Mini-cart · Presence · Skeleton · PTR · Undo

## Nested systems

Commerce · SaaS admin · Social · Messaging · Work board · Booking · Content site

## Residuals (MORE_CASES)

Tree · Lightbox · Map+panel · Inline edit · Tags · Date range · Theme/locale/currency · Session gate · Tour · Offline queue · Tenant switcher · Versions · Approval · Coupon · KYC · Share · Split pane · PDP variants/qty/stars · Watch · Attachments · Diff · Timeline · FAB · Bottom nav · Magic link · Captcha gate · Maintenance

## Encoding rule for anything new

```text
Open/value/query/list window  → MorphState
Tokens/pending/target ids     → RefState
One-shot message              → notify
Domain money/stock            → Host DB (not client plane)
Multi-unit open               → Host orchestrate dispatches
```

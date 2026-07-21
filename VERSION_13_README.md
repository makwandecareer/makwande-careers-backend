# Makwande Careers Frontend v13 — Template Process Integration

The existing layouts were not redesigned.

This release adds the working process:

1. A client selects any of the 50 templates.
2. The selection is saved in browser storage.
3. CV Studio detects the selected template.
4. Template layout, colours, fonts, header style and photo preference are applied.
5. The selected template becomes the active CV Studio template.
6. Autosave preserves the template and CV content.
7. PDF and DOCX export requests now include the complete template and design configuration.
8. Returning to the template library restores the selected template.

Open:

- `/dashboard/templates`
- Select a template
- Click `Use this template`
- CV Studio opens with the selected design active

---
name: minimalist-ui-design
description: This skill provides guidance for implementing the Thor Electric minimalist UI design system. Use this skill when styling Django templates with Tailwind CSS to maintain consistency across the application with clean, professional aesthetics featuring black buttons, light typography, white cards, and Heroicons.
context: fork
---

# Minimalist UI Design System

This skill documents the minimalist design pattern used throughout the Thor Electric application. Apply these patterns when creating or updating Django templates to ensure visual consistency and professional aesthetics.

## When to Use This Skill

Use this skill when:
- Creating new Django templates for Thor Electric
- Updating existing pages to match the minimalist design system
- Implementing forms, lists, cards, or navigation elements
- Adding search bars, buttons, or interactive components
- Converting designs from gradients/shadows to clean minimalist style

## Core Design Principles

### 1. Typography
- **Headers**: Use `font-light` (not font-bold or font-black) with `tracking-tight` for clean, modern appearance
- **Body text**: Use `text-sm text-gray-500` for secondary information
- **Primary text**: Use `text-gray-900` for main content
- **Examples**:
  ```html
  <h1 class="text-3xl font-light text-gray-900 tracking-tight mb-2">Page Title</h1>
  <p class="text-sm text-gray-500">Subtitle or description</p>
  ```

### 2. Buttons

#### Primary Action Buttons (Black)
Use for main actions like "Add", "Create", "Save", "Submit":
```html
<button class="inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-xl text-white bg-gray-900 hover:bg-gray-800 transition-all duration-200">
    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15"/>
    </svg>
    Add Item
</button>
```

#### Secondary Action Buttons (White with Gray Border)
Use for secondary actions like "View", "Cancel":
```html
<button class="px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium rounded-xl transition-colors duration-200 text-sm">
    View
</button>
```

#### Icon-Only Buttons
For actions in tight spaces:
```html
<button class="w-8 h-8 flex items-center justify-center text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>
</button>
```

### 3. Cards
Replace gradient backgrounds and heavy shadows with clean white cards and gray borders:

```html
<div class="bg-white rounded-2xl border border-gray-200 hover:border-gray-300 transition-all duration-200 p-6">
    <!-- Card content -->
</div>
```

**Before (Old Style)**:
```html
<div class="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg p-6">
```

**After (New Style)**:
```html
<div class="bg-white rounded-2xl border border-gray-200 p-6">
```

### 4. Search Bars (Flexbox Pattern)

All search bars should use this consistent pattern:

```html
<div class="flex items-center bg-white border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-gray-200 focus-within:border-gray-300 transition-all">
    <div class="pl-4 text-gray-400">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
    </div>
    <input type="text" placeholder="Search..."
           class="flex-1 px-3 py-3 pr-4 bg-transparent border-0 focus:outline-none text-sm text-gray-900 placeholder-gray-500"/>
</div>
```

**Key Features**:
- White background with gray border
- Icon container uses padding-left (pl-4) instead of absolute positioning
- Input uses flex-1 to fill remaining space
- Gray focus states (no colored rings)
- Transparent input background

### 5. Icons

#### Use Heroicons (Inline SVG)
Replace all Feather icons with Heroicons:

**Search Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
</svg>
```

**Plus Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15"/>
</svg>
```

**Arrow Left Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
</svg>
```

**X (Close) Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
</svg>
```

**Info Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
</svg>
```

**Hash (Channel) Icon**:
```html
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/>
</svg>
```

### 6. Form Inputs

#### Text Inputs & Dropdowns
```html
<input type="text"
       class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-200 focus:border-gray-300 text-sm"/>

<select class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-200 focus:border-gray-300 text-sm">
    <option>Option 1</option>
</select>
```

**Key Features**:
- Gray borders (border-gray-200)
- Gray focus states (no colored rings)
- Rounded corners (rounded-xl)
- Consistent padding (px-4 py-3)

#### Enhanced Date Picker with Flatpickr

For clean, minimalist date selection, use Flatpickr instead of default browser date inputs:

**1. Add Flatpickr CDN to template** (in `{% block extra_head %}`):
```html
{% block extra_head %}
<!-- Flatpickr CSS and JS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>

<!-- Custom Flatpickr Minimalist Styling -->
<style>
    .flatpickr-calendar {
        border-radius: 12px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
    }
    .flatpickr-day.selected {
        background: #111827 !important;
        border-color: #111827 !important;
    }
    .flatpickr-day.selected:hover {
        background: #1f2937 !important;
        border-color: #1f2937 !important;
    }
    .flatpickr-day:hover {
        background: #f3f4f6 !important;
        border-color: transparent !important;
    }
    .flatpickr-months .flatpickr-month {
        background: white !important;
        border-bottom: 1px solid #e5e7eb;
    }
    .flatpickr-current-month .flatpickr-monthDropdown-months {
        background: white !important;
    }
    .flatpickr-current-month input.cur-year {
        font-weight: 400 !important;
    }
</style>
{% endblock %}
```

**2. Initialize Flatpickr** (in your JavaScript):
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Find all date inputs and apply Flatpickr
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        flatpickr(input, {
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "F j, Y",
            allowInput: true,
            disableMobile: false,
            theme: "light"
        });
    });
});
```

**Result**: Clean calendar picker with:
- Rounded corners matching your design system
- Gray borders and subtle shadows
- Black selected date (matching button style)
- Light gray hover states
- Human-readable date display ("January 15, 2025")

#### Enhanced Dropdowns with Choices.js

For searchable, clean dropdowns instead of default browser selects:

**1. Add Choices.js CDN to template** (in `{% block extra_head %}`):
```html
{% block extra_head %}
<!-- Choices.js CSS and JS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js/public/assets/styles/choices.min.css">
<script src="https://cdn.jsdelivr.net/npm/choices.js/public/assets/scripts/choices.min.js"></script>

<!-- Custom Choices.js Minimalist Styling -->
<style>
    .choices__inner {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1rem !important;
        min-height: 42px !important;
        font-size: 0.875rem !important;
        transition: all 0.2s !important;
    }
    .choices__inner:hover {
        border-color: #d1d5db !important;
    }
    .choices.is-focused .choices__inner {
        border-color: #d1d5db !important;
        box-shadow: 0 0 0 3px #f3f4f6 !important;
    }
    .choices__list--dropdown .choices__item--selectable {
        padding: 0.75rem 1rem !important;
        font-size: 0.875rem !important;
    }
    .choices__list--dropdown .choices__item--selectable.is-highlighted {
        background-color: #f3f4f6 !important;
    }
    .choices__input {
        background: transparent !important;
        font-size: 0.875rem !important;
        margin-bottom: 0 !important;
        padding: 0.25rem 0 !important;
    }
    .choices__placeholder {
        color: #9ca3af !important;
        opacity: 1 !important;
    }
</style>
{% endblock %}
```

**2. Initialize Choices.js BEFORE attaching event listeners**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Choices.js on select elements FIRST
    const mySelect = document.getElementById('mySelectElement');
    let myChoices = null;

    if (mySelect) {
        // Initialize Choices.js to transform the select
        myChoices = new Choices(mySelect, {
            searchEnabled: true,
            shouldSort: false,
            placeholder: true,
            placeholderValue: 'Choose an option...',
            searchPlaceholderValue: 'Search...',
            allowHTML: false,
            itemSelectText: '',
            noResultsText: 'No results found',
            noChoicesText: 'No options available',
        });

        // THEN attach event listeners AFTER Choices.js initialization
        mySelect.addEventListener('change', function() {
            const value = this.value;
            // Handle change event
        });
    }
});
```

**IMPORTANT**: Always initialize Choices.js BEFORE attaching event listeners to the select element. If you attach events first, they'll be attached to the raw select before Choices.js transforms it.

**Result**: Professional searchable dropdowns with:
- Clean rounded borders matching your design system
- Search functionality built-in
- Smooth animations and transitions
- Gray color palette (no bright colors)
- Keyboard navigation support
- Mobile-friendly

### 7. Icon Containers

For decorative icon containers (in cards, headers, etc.):

**Black Background** (Primary):
```html
<div class="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center">
    <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <!-- icon path -->
    </svg>
</div>
```

**Before (Old Style - Gradients)**:
```html
<div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl">
```

**After (New Style - Black)**:
```html
<div class="w-12 h-12 bg-gray-900 rounded-xl">
```

### 8. Filter Sections

Filter panels should use clean white backgrounds:

```html
<div class="bg-white rounded-2xl border border-gray-200 p-6 mb-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- Filter inputs -->
    </div>
</div>
```

### 9. Color Palette

**Primary Colors**:
- Black buttons: `bg-gray-900` with `hover:bg-gray-800`
- Card backgrounds: `bg-white`
- Card borders: `border-gray-200`
- Hover borders: `hover:border-gray-300`

**Text Colors**:
- Primary headings: `text-gray-900`
- Body text: `text-gray-700`
- Secondary text: `text-gray-500`
- Placeholder text: `placeholder-gray-500`
- Icons: `text-gray-400` or `text-gray-600`

**Status Colors** (Keep these):
- Success: `bg-emerald-50 text-emerald-700 border-emerald-200`
- Warning: `bg-orange-50 text-orange-700 border-orange-200`
- Error: `bg-red-50 text-red-700 border-red-200`
- Info: `bg-blue-50 text-blue-700 border-blue-200`

### 10. Navigation Active States

For sidebar navigation, use conditional highlighting:

```html
<a href="{% url 'core:dashboard' %}"
   class="nav-item group flex items-center px-4 py-3.5 text-sm font-semibold rounded-2xl transition-all duration-200
   {% if request.resolver_match.url_name == 'dashboard' %}
       bg-gradient-to-r from-primary-500/20 to-emerald-500/20 text-white shadow-lg border border-primary-500/20 active
   {% else %}
       text-slate-300 hover:bg-white/5 hover:text-white hover:shadow-lg hover:border-white/10 border border-transparent
   {% endif %}">
    <div class="w-6 h-6 mr-4 flex items-center justify-center rounded-lg
         {% if request.resolver_match.url_name == 'dashboard' %}
             bg-primary-500/30 text-primary-300
         {% else %}
             group-hover:bg-white/10
         {% endif %}
         transition-all duration-200">
        <!-- icon -->
    </div>
    <span class="flex-1">Dashboard</span>
    {% if request.resolver_match.url_name == 'dashboard' %}
        <div class="w-2 h-2 bg-primary-400 rounded-full shadow-lg"></div>
    {% endif %}
</a>
```

## Common Patterns

### List/Grid with Action Buttons
```html
<div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    {% for item in items %}
    <div class="bg-white rounded-2xl border border-gray-200 hover:border-gray-300 transition-all duration-200 p-6">
        <h3 class="text-base font-medium text-gray-900 mb-2">{{ item.name }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ item.description }}</p>

        <div class="flex gap-2">
            <button class="flex-1 px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium rounded-xl transition-colors duration-200 text-sm">
                View
            </button>
            <button class="flex-1 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white font-medium rounded-xl transition-colors duration-200 text-sm">
                Edit
            </button>
        </div>
    </div>
    {% endfor %}
</div>
```

### Page Header with Action Button
```html
<div class="mb-8">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-3xl font-light text-gray-900 tracking-tight mb-2">Page Title</h1>
            <p class="text-sm text-gray-500">Description of the page content</p>
        </div>
        <div class="flex gap-3">
            <button class="inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-xl text-white bg-gray-900 hover:bg-gray-800 transition-all duration-200">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15"/>
                </svg>
                Add New
            </button>
        </div>
    </div>
</div>
```

### Empty State
```html
<div class="text-center py-12">
    <div class="w-24 h-24 mx-auto bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
        <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <!-- icon -->
        </svg>
    </div>
    <h3 class="text-base font-medium text-gray-900 mb-2">No items found</h3>
    <p class="text-sm text-gray-500 mb-6">Get started by adding your first item.</p>
    <button class="inline-flex items-center px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white font-medium rounded-xl transition-colors duration-200 text-sm">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        Add Item
    </button>
</div>
```

## Migration Checklist

When updating an existing page to the minimalist design:

- [ ] Change `font-bold` or `font-black` headers to `font-light` with `tracking-tight`
- [ ] Replace gradient buttons with `bg-gray-900 hover:bg-gray-800`
- [ ] Update cards from `shadow-lg` to `border border-gray-200`
- [ ] Convert search bars to flexbox pattern
- [ ] Replace Feather icons with Heroicons (inline SVG)
- [ ] Update form inputs to gray borders and focus states
- [ ] Change icon containers from gradients to black (`bg-gray-900`)
- [ ] Update dropdown borders from colored to gray
- [ ] Ensure all text uses appropriate gray shades
- [ ] Remove any remaining gradient backgrounds

## Examples

See these successfully implemented pages:
- Materials Catalog (`core/templates/materials/materials_list.html`)
- Quote Form (`financial/templates/financial/quote_form.html`)
- Team Channels (`messaging/templates/messaging/team_channels.html`)
- Channel Detail (`messaging/templates/messaging/channel_detail.html`)

## Notes

- **Avoid emojis**: Don't use emojis in templates unless explicitly requested by the user
- **Keep accessibility**: Maintain proper ARIA labels and semantic HTML
- **Responsive design**: Ensure mobile-first responsive layouts work correctly
- **Consistency is key**: The goal is visual consistency across all pages

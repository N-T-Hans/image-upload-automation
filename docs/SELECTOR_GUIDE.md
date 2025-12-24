# CSS Selector Discovery Guide

Learn how to find CSS selectors for CardDealerPro form elements using Chrome DevTools.

## What Are CSS Selectors?

CSS selectors are patterns used to identify HTML elements on a webpage. Examples:
- `#username` - Element with id="username"
- `.button-primary` - Elements with class="button-primary"
- `input[name="email"]` - Input element with name="email"
- `button[type="submit"]` - Button element with type="submit"

## Tools You Need

- **Google Chrome Browser** (recommended)
- **Chrome DevTools** (built into Chrome, press F12)

## Step-by-Step Guide

### Step 1: Open Chrome DevTools

1. Open Google Chrome
2. Navigate to carddealerpro.com
3. Press **F12** (or right-click anywhere → "Inspect")
4. DevTools panel opens (usually at bottom or right side)

### Step 2: Locate an Element

There are two methods:

#### Method A: Right-Click Inspect (Easier)

1. Right-click directly on the element you want (e.g., username field)
2. Choose **"Inspect"** from menu
3. DevTools highlights the element's HTML code

#### Method B: Element Picker (More Precise)

1. Click the **"Select an element"** icon in DevTools (top-left corner)
2. Hover over elements on the page (they highlight in blue)
3. Click the element you want
4. DevTools highlights its HTML code

### Step 3: Copy the CSS Selector

Once an element is highlighted in DevTools:

1. The HTML element is highlighted in the **Elements** tab
2. Right-click on the highlighted HTML line
3. Choose **Copy** → **Copy selector**
4. Paste into your config file

**Example:**
```
Highlighted: <input type="text" name="username" id="user-input" class="form-control">
Copied selector: #user-input
```

### Step 4: Test the Selector

**IMPORTANT**: Always test selectors before using them!

1. In DevTools, click the **Console** tab
2. Type: `document.querySelector('your-selector-here')`
3. Press Enter

**Example:**
```javascript
document.querySelector('#user-input')
// Should return: <input type="text" name="username" ...>

// If it returns null, the selector is wrong!
document.querySelector('#wrong-selector')
// Returns: null
```

### Step 5: Verify Uniqueness

Your selector should find **exactly one** element:

```javascript
// Good: Returns 1 element
document.querySelectorAll('#username').length
// Returns: 1

// Bad: Returns multiple elements
document.querySelectorAll('.button').length
// Returns: 15 (too many! Need more specific selector)
```

## Finding Selectors for Different Element Types

### Text Inputs

**Look for:**
- `input[type="text"]`
- `input[name="field_name"]`
- `#field-id`
- `.specific-class`

**Example HTML:**
```html
<input type="text" name="batch_name" id="batch-name-input" class="form-control">
```

**Possible selectors:**
- `#batch-name-input` (best - unique ID)
- `input[name="batch_name"]` (good - unique name)
- `input.form-control` (bad - not unique)

### Dropdown Selects

**Look for:**
- `select[name="field_name"]`
- `#select-id`
- `select.specific-class`

**Example HTML:**
```html
<select name="sport_type" id="sport-select" class="form-select">
  <option>Baseball</option>
  <option>Basketball</option>
</select>
```

**Best selector:**
- `#sport-select` or `select[name="sport_type"]`

### Custom Dropdowns (Headless UI)

Some dropdowns are implemented with custom components (not native `<select>`). For these:

- Use the button element that opens the listbox (often `aria-haspopup="listbox"`).
- In `selectors`, add the `_select` key and set an accompanying `_select_type` to `"custom"`.

**Config examples:**
```json
{
  "selectors": {
    "title_template_select": "button[aria-haspopup='listbox'][data-testid='title-template']",
    "title_template_select_type": "custom",

    "description_template_select": "button[aria-haspopup='listbox'][data-testid='description-template']",
    "description_template_select_type": "custom",

    "optional_condition": "button[aria-haspopup='listbox'][data-testid='condition']",
    "optional_condition_type": "custom",

    "optional_sale_price": "input[name='sale_price']"
  }
}
```

With these settings, the workflow will open the custom dropdown and click the matching option by visible text.

### Buttons

**Look for:**
- `button[type="submit"]`
- `button.button-class`
- `#button-id`
- `button:contains('Text')` (not standard CSS, use data attributes instead)

**Example HTML:**
```html
<button type="submit" class="btn btn-primary" id="continue-btn">
  Continue
</button>
```

**Best selector:**
- `#continue-btn` (most specific)
- `button[type="submit"]` (may match multiple)

⚠️ **Multiple submit buttons?** Use more specific selectors:
```javascript
// If there are multiple submit buttons, be more specific:
document.querySelector('.general-settings-form button[type="submit"]')
```

### File Upload Inputs

File inputs are often **hidden** visually but still in the DOM.

**Look for:**
- `input[type="file"]`
- `input[name="files"]`
- `input[accept*="image"]`

**Finding hidden file inputs:**

1. In DevTools Elements tab, press **Ctrl+F** (Cmd+F on Mac)
2. Search for: `type="file"`
3. Find all file input elements
4. Copy selector for the one on the upload page

**Example HTML:**
```html
<input type="file" name="images" multiple accept="image/*" style="display:none">
```

**Selector:**
- Prefer a stable hidden input: e.g., `input#searchImage[type="file"]`
  - The workflow detects hidden file inputs and sends file paths directly.

## Common Selector Patterns

### Using ID (Best - Most Specific)
```css
#username
#password-field
#submit-button
```

### Using Name Attribute (Good)
```css
input[name="username"]
select[name="batch_type"]
button[name="submit"]
```

### Using Class (Be Careful - May Not Be Unique)
```css
.login-button
.form-control.username
button.btn-primary
```

### Using Data Attributes (Excellent - Often Unique)
```css
[data-testid="login-button"]
[data-action="submit"]
button[data-step="continue"]
```

### Combining Selectors (More Specific)
```css
form.login-form input[name="username"]
div.settings-panel select[name="batch_type"]
.upload-section button[type="submit"]
```

## CardDealerPro Specific Examples

### Login Page

**Username field:**
```javascript
// Try these in order until one works:
document.querySelector('input[type="email"]')
document.querySelector('input[name="username"]')
document.querySelector('#username')
document.querySelector('.username-input')
```

**Password field:**
```javascript
document.querySelector('input[type="password"]')
document.querySelector('input[name="password"]')
document.querySelector('#password')
```

**Login button:**
```javascript
document.querySelector('button[type="submit"]')
document.querySelector('.login-button')
document.querySelector('button.btn-primary')
```

### Batches Page

**Create batch button:**
```javascript
// Look for buttons with relevant text or classes
document.querySelector('button.create-batch')
document.querySelector('a[href*="create-batch"]')
document.querySelector('button:has-text("Create Batch")') // Not standard CSS
```

### General Settings Page

**Batch name:**
```javascript
document.querySelector('input[name="batch_name"]')
document.querySelector('#batch-name')
```

**Dropdowns:**
```javascript
document.querySelector('select[name="batch_type"]')
document.querySelector('select[name="sport_type"]')
document.querySelector('#sport-select')
```

## Troubleshooting Selectors

### Problem: Selector returns `null`

**Solutions:**
1. Element might not be loaded yet (wait for page load)
2. Selector is incorrect (typo or wrong syntax)
3. Element is in an iframe (need different approach)
4. Element hasn't appeared yet (triggered by JavaScript)

**Debug:**
```javascript
// Check if element exists anywhere on page
document.body.innerHTML.includes('username')

// See all input elements
document.querySelectorAll('input')

// See all buttons
document.querySelectorAll('button')
```

### Problem: Selector returns multiple elements

**Solutions:**
1. Make selector more specific
2. Add parent context
3. Use unique ID or data attribute

**Example:**
```javascript
// Too broad:
document.querySelectorAll('button')  // Returns: 20 buttons

// More specific:
document.querySelectorAll('.modal button.submit')  // Returns: 1 button
```

### Problem: Selector works in console but fails in script

**Possible causes:**
1. **Timing issue** - Element not loaded when script runs
   - Solution: Script uses WebDriverWait for elements
   
2. **Dynamic content** - Element ID/class changes
   - Solution: Use more stable attributes (name, data-*)
   
3. **Different page state** - Manual testing had different page state
   - Solution: Test in same sequence as script

## Best Practices

### ✅ DO:
- Use IDs when available (`#username`)
- Use name attributes (`input[name="username"]`)
- Use data attributes (`[data-testid="login"]`)
- Test selectors in console before using
- Be as specific as necessary (not more)
- Document selectors for future reference

### ❌ DON'T:
- Rely on index positions (`.form-group:nth-child(3)`)
- Use auto-generated classes (`._1a2b3c4d`)
- Use overly complex selectors
- Assume selectors won't change (website updates can break them)

## Selector Maintenance

Websites change! If selectors stop working:

1. **Visit the website** and check if layout changed
2. **Re-inspect elements** to find new selectors
3. **Update config file** with new selectors
4. **Test immediately** to verify

## Testing Your Selectors

Before running the full workflow, test each selector:

```javascript
// Create a selector testing script in browser console:

const selectors = {
  username: 'input[name="username"]',
  password: 'input[type="password"]',
  loginButton: 'button[type="submit"]',
  // ... add all your selectors
};

Object.entries(selectors).forEach(([name, selector]) => {
  const element = document.querySelector(selector);
  console.log(
    element ? `✓ ${name}: FOUND` : `✗ ${name}: NOT FOUND`,
    selector
  );
});
```

## Visual Guide

Here's what you'll see in DevTools:

```
┌─────────────────────────────────────────────────┐
│ Elements    Console    Network    ...          │ ← Tabs
├─────────────────────────────────────────────────┤
│ <html>                                          │
│   <body>                                        │
│     <div class="login-page">                    │
│       <form class="login-form">                 │
│         <input type="text" name="username"> ←─── Right-click here
│         <input type="password" name="password"> │
│         <button type="submit">Login</button>    │
│       </form>                                   │
│     </div>                                      │
│   </body>                                       │
│ </html>                                         │
└─────────────────────────────────────────────────┘
```

## Next Steps

Once you have all your selectors:

1. **Add them to your config file** (`my_batch.json`)
2. **Test the script** with a small batch
3. **Adjust selectors** if any fail
4. **Document working selectors** for future use

---

**Need more help?** 
- Check [USAGE.md](USAGE.md) for error messages
- Review [QUICKSTART.md](QUICKSTART.md) for setup issues

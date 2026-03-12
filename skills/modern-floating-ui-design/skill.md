---
name: modern-floating-ui-design
description: Modern Floating UI Design System
---

# Modern Floating UI Design System

You are a React Native/Mobile UI expert specializing in a clean, modern, floating design system that works for **ANY mobile application** - e-commerce, social media, productivity, finance, health, education, and more.

## Design Philosophy

This is a **Universal Modern iOS-Inspired Material Design** system featuring:
- **Floating pill-shaped navigation bars** - works for any app with bottom navigation
- **Soft shadows and subtle elevation** - creates depth without being heavy
- **Rounded corners everywhere** (15-20px for cards) - friendly, approachable feel
- **White cards on light gray backgrounds** - clean separation of content
- **Clean, minimal, professional aesthetics** - suitable for any industry
- **Semi-transparent overlays** for glass-morphic effects - modern, polished look

**This design system is framework-agnostic and can be applied to:**
- React Native apps
- Flutter apps
- Swift/SwiftUI (iOS native)
- Kotlin/Jetpack Compose (Android native)
- Any mobile application framework

**Perfect for:**
- E-commerce & marketplaces
- Social media & community apps
- Productivity & task management
- Finance & banking apps
- Health & fitness tracking
- Education & learning platforms
- Real estate & property apps
- Service booking & scheduling
- Food delivery & restaurant apps
- Travel & booking apps

## Core Theme System

### Color Palette

**Primary Colors (Customizable):**
```javascript
// Example: Deep navy blue (change to match your brand)
primary: '#0C125B'        // Main brand color - can be any color
primaryLight: '#1A237E'   // Lighter variant - 20% lighter
primaryDark: '#000051'    // Darker variant - 20% darker

// Other brand color examples you can use:
// Blue: '#2563EB' (Modern tech apps)
// Purple: '#7C3AED' (Creative apps)
// Green: '#059669' (Health/Finance apps)
// Orange: '#EA580C' (Food/Social apps)
// Pink: '#DB2777' (Fashion/Beauty apps)
// Teal: '#0D9488' (Productivity apps)
```

**Grayscale System:**
```javascript
gray50: '#fafafa'    // Screen backgrounds
gray100: '#f5f5f5'   // Input backgrounds, inactive buttons
gray200: '#eeeeee'   // Borders, dividers
gray300: '#e0e0e0'   // Inactive states
gray400: '#bdbdbd'   // Disabled text
gray500: '#9e9e9e'   // Placeholder text, icon colors
gray600: '#757575'   // Secondary text
gray700: '#616161'   // Primary text (light theme)
gray800: '#424242'   // Dark surfaces
gray900: '#212121'   // Primary text (dark theme)
```

**Status Colors:**
```javascript
success: '#2E7D32'   // Green for verified, success
error: '#ff4757'     // Red for errors
warning: '#ffa726'   // Orange for warnings
info: '#29b6f6'      // Blue for info
```

### Typography Scale

```javascript
fontSize: {
  xs: 12,      // Badges, helper text
  sm: 14,      // Secondary text, captions
  base: 16,    // Body text, inputs
  lg: 18,      // Subheadings
  xl: 20,      // Section titles
  '2xl': 24,   // Card titles
  '3xl': 28,   // Page titles
  '4xl': 32,   // Hero text
  '5xl': 36    // Emphasis
}

fontWeight: {
  normal: '400',
  medium: '500',
  semiBold: '600',
  bold: '700'
}
```

### Spacing System (4px Grid)

```javascript
spacing: {
  xs: 4,       // Micro spacing
  sm: 8,       // Tight spacing
  md: 12,      // Compact spacing
  base: 16,    // Default spacing (most common)
  lg: 20,      // Comfortable spacing
  xl: 24,      // Spacious
  '2xl': 32,   // Section spacing
  '3xl': 48,   // Major sections
  '4xl': 64    // Screen margins
}
```

### Border Radius Strategy

```javascript
borderRadius: {
  none: 0,      // Sharp corners
  sm: 4,        // Subtle rounding
  base: 8,      // Default rounding
  md: 10,       // Buttons, filters
  lg: 12,       // Input fields
  xl: 15,       // Standard cards
  '2xl': 20,    // Large cards, headers
  full: 9999    // Pills, circles
}
```

**Usage Pattern:**
- Cards: `xl` to `2xl` (15-20px)
- Buttons: `md` to `full` (10px to pill shape)
- Inputs: `xl` (15px)
- Icons/Avatars: `full` for perfect circles
- Badges: `full` for pill shapes

### Shadow/Elevation System

```javascript
// Subtle - for inputs
sm: {
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.1,
  shadowRadius: 2,
  elevation: 2
}

// Default - for cards
base: {
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.1,
  shadowRadius: 3.84,
  elevation: 5
}

// Medium - for modals
md: {
  shadowOffset: { width: 0, height: 4 },
  shadowOpacity: 0.15,
  shadowRadius: 6,
  elevation: 8
}

// Strong - for floating elements (tab bar, FAB)
lg: {
  shadowOffset: { width: 0, height: 8 },
  shadowOpacity: 0.2,
  shadowRadius: 10,
  elevation: 12
}
```

**Key Principle:** Always use subtle shadows (0.1-0.15 opacity) with vertical-only offsets

## Component Patterns

### 1. Floating Pill-Shaped Tab Bar

```javascript
tabBarStyle: {
  backgroundColor: theme.colors.white,
  borderTopWidth: 0,
  paddingBottom: 8,
  paddingTop: 8,
  paddingHorizontal: 20,
  height: 65,
  position: 'absolute',        // FLOATING
  bottom: 40,                  // Lifted from bottom
  left: 40,
  right: 40,
  marginHorizontal: 20,
  borderRadius: 32,            // PILL SHAPE
  shadowColor: theme.colors.black,
  shadowOffset: { width: 0, height: 6 },
  shadowOpacity: 0.2,
  shadowRadius: 15,
  elevation: 20               // High elevation
}
```

**Active Tab Indicator:**
```javascript
// Circle background for active state
if (focused) {
  return (
    <View style={{
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: theme.colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Ionicons name={iconName} size={size} color={theme.colors.white} />
    </View>
  );
}
```

### 2. Property Card Design

```javascript
// Container - white card with rounded corners
container: {
  backgroundColor: theme.colors.white,
  borderRadius: theme.borderRadius['2xl'],  // 20px
  marginBottom: theme.spacing.lg,
  overflow: 'hidden',
  ...theme.elevation.base
}

// Image section
imageContainer: {
  position: 'relative',
  height: 200,
  backgroundColor: theme.colors.gray200
}

// Floating action buttons over image
actionButtons: {
  position: 'absolute',
  bottom: theme.spacing.md,
  right: theme.spacing.md,
  flexDirection: 'row',
  gap: theme.spacing.sm
}

actionButton: {
  width: 40,
  height: 40,
  borderRadius: 20,
  backgroundColor: 'rgba(255, 255, 255, 0.9)',  // Glass effect
  alignItems: 'center',
  justifyContent: 'center',
  ...theme.elevation.sm
}

// Badges on images
badge: {
  position: 'absolute',
  top: theme.spacing.md,
  right: theme.spacing.md,
  backgroundColor: 'rgba(0, 0, 0, 0.6)',
  paddingHorizontal: theme.spacing.sm,
  paddingVertical: theme.spacing.xs,
  borderRadius: theme.borderRadius.full,
  flexDirection: 'row',
  alignItems: 'center',
  gap: 4
}
```

### 3. Input Field Design

```javascript
textInput: {
  backgroundColor: theme.colors.input.background,
  borderWidth: 1,
  borderColor: theme.colors.input.border,
  borderRadius: theme.borderRadius.xl,        // 15px
  paddingHorizontal: theme.spacing.base,
  paddingVertical: theme.spacing.md,
  fontSize: theme.typography.fontSize.base,
  color: theme.colors.input.text,
  ...theme.elevation.sm                       // Subtle shadow
}

// Focus state
textInputFocused: {
  borderColor: theme.colors.input.borderFocus,  // Primary color
  borderWidth: 2
}
```

### 4. Button Patterns

**Primary Button (Pill Shape):**
```javascript
primaryButton: {
  backgroundColor: theme.colors.button.primary.background,
  borderRadius: theme.borderRadius.full,      // Pill shape
  paddingVertical: 18,
  paddingHorizontal: theme.spacing.xl,
  alignItems: 'center',
  justifyContent: 'center',
  ...theme.elevation.sm
}

primaryButtonText: {
  color: theme.colors.white,
  fontSize: theme.typography.fontSize.base,
  fontWeight: theme.typography.fontWeight.semiBold
}
```

**Secondary Button (Outline):**
```javascript
secondaryButton: {
  backgroundColor: 'transparent',
  borderWidth: 1,
  borderColor: theme.colors.primary,
  borderRadius: theme.borderRadius.md,
  paddingVertical: theme.spacing.base,
  paddingHorizontal: theme.spacing.lg,
  alignItems: 'center',
  justifyContent: 'center'
}
```

**Icon Button (Circle):**
```javascript
iconButton: {
  width: 40,
  height: 40,
  borderRadius: 20,                          // Perfect circle
  backgroundColor: theme.colors.gray100,
  alignItems: 'center',
  justifyContent: 'center'
}
```

### 5. Header Design

```javascript
header: {
  backgroundColor: theme.colors.white,
  paddingHorizontal: theme.spacing.lg,
  paddingTop: theme.spacing['2xl'],
  paddingBottom: theme.spacing.lg,
  borderBottomLeftRadius: theme.borderRadius['2xl'],   // Curved bottom
  borderBottomRightRadius: theme.borderRadius['2xl'],
  ...theme.elevation.sm
}
```

### 6. Search Bar Pattern

```javascript
searchInputContainer: {
  flex: 1,
  flexDirection: 'row',
  alignItems: 'center',
  backgroundColor: theme.colors.gray100,
  borderRadius: theme.borderRadius.xl,       // 15px
  paddingHorizontal: theme.spacing.base,
  paddingVertical: theme.spacing.sm
}

searchIcon: {
  marginRight: theme.spacing.sm
}

searchInput: {
  flex: 1,
  fontSize: theme.typography.fontSize.base,
  color: theme.colors.text.primary
}
```

### 7. Modal/Bottom Sheet Design

```javascript
modalOverlay: {
  flex: 1,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',    // 50% dark overlay
  justifyContent: 'flex-end'
}

modalContainer: {
  backgroundColor: theme.colors.white,
  borderTopLeftRadius: 24,                  // Only top corners
  borderTopRightRadius: 24,
  maxHeight: '80%',
  paddingBottom: 30                         // Safe area
}

modalHeader: {
  flexDirection: 'row',
  justifyContent: 'space-between',
  alignItems: 'center',
  paddingHorizontal: 20,
  paddingVertical: 16,
  borderBottomWidth: 1,
  borderBottomColor: theme.colors.gray100
}
```

### 8. Floating Action Button (FAB)

```javascript
fabContainer: {
  position: 'absolute',
  bottom: 120,                    // Above tab bar
  right: 20,
  zIndex: 1000
}

fabButton: {
  width: 56,
  height: 56,
  borderRadius: 28,               // Perfect circle
  backgroundColor: theme.colors.primary,
  alignItems: 'center',
  justifyContent: 'center',
  ...theme.elevation.lg           // Strong shadow
}
```

### 9. Badge Designs

**Status Badge:**
```javascript
statusBadge: {
  paddingHorizontal: 8,
  paddingVertical: 2,
  borderRadius: 12,               // Pill shape
  flexDirection: 'row',
  alignItems: 'center',
  gap: 4,
  alignSelf: 'flex-start'
}
```

**Floating Badge on Image:**
```javascript
floatingBadge: {
  position: 'absolute',
  top: theme.spacing.md,
  right: theme.spacing.md,
  backgroundColor: 'rgba(0, 0, 0, 0.6)',
  paddingHorizontal: theme.spacing.sm,
  paddingVertical: theme.spacing.xs,
  borderRadius: theme.borderRadius.full
}
```

### 10. Empty State Pattern

```javascript
emptyState: {
  backgroundColor: theme.colors.card,
  padding: theme.spacing.xl,
  borderRadius: theme.borderRadius.xl,
  alignItems: 'center',
  ...theme.elevation.base
}

emptyStateIcon: {
  marginBottom: theme.spacing.base
  // Use Ionicons, size 48, color gray400
}

emptyStateTitle: {
  fontSize: theme.typography.fontSize.lg,
  fontWeight: theme.typography.fontWeight.bold,
  color: theme.colors.text.primary,
  marginBottom: theme.spacing.sm,
  textAlign: 'center'
}

emptyStateText: {
  fontSize: theme.typography.fontSize.base,
  color: theme.colors.text.secondary,
  textAlign: 'center',
  lineHeight: 22
}
```

## Screen Layout Patterns

### Standard Screen Structure

```javascript
<View style={styles.container}>
  <ScrollView
    showsVerticalScrollIndicator={false}
    contentContainerStyle={styles.scrollContent}
  >
    {/* Header */}
    <View style={styles.header}>
      {/* Logo, navigation, notifications */}
    </View>

    {/* Main Content */}
    <View style={styles.content}>
      {/* Cards, lists, grids */}
    </View>
  </ScrollView>
</View>

// Styles
container: {
  flex: 1,
  backgroundColor: theme.colors.screen.primary  // gray50
}

header: {
  backgroundColor: theme.colors.white,
  borderBottomLeftRadius: theme.borderRadius['2xl'],
  borderBottomRightRadius: theme.borderRadius['2xl'],
  ...theme.elevation.sm
}

content: {
  paddingHorizontal: theme.spacing.lg,
  paddingTop: theme.spacing.xl,
  paddingBottom: 120                          // Floating tab bar clearance
}
```

### Grid Layout (2 Columns)

```javascript
const cardWidth = (width - 48) / 2;  // Account for padding and gap

<FlatList
  data={properties}
  numColumns={2}
  columnWrapperStyle={styles.row}
  contentContainerStyle={styles.gridContent}
  renderItem={({ item }) => <PropertyCard property={item} />}
/>

// Styles
row: {
  justifyContent: 'space-between',
  marginBottom: theme.spacing.lg
}

gridContent: {
  paddingHorizontal: theme.spacing.lg,
  paddingTop: theme.spacing.lg,
  paddingBottom: 120
}
```

## Animation Patterns

### Screen Transitions

```javascript
// Stack navigator animations
screenOptions: {
  animation: 'slide_from_right',
  animationDuration: 300,
  gestureEnabled: true,
  gestureDirection: 'horizontal',
  fullScreenGestureEnabled: true
}

// Modal presentations
presentation: 'modal',
animation: 'slide_from_bottom',
gestureDirection: 'vertical'
```

### Touch Feedback

```javascript
<TouchableOpacity
  activeOpacity={0.7}      // Subtle opacity change
  onPress={handlePress}
>
  {/* Button content */}
</TouchableOpacity>
```

## Image Handling Patterns

### Cover Images

```javascript
coverImage: {
  width: '100%',
  height: 200,
  backgroundColor: theme.colors.gray200,
  borderTopLeftRadius: theme.borderRadius['2xl'],
  borderTopRightRadius: theme.borderRadius['2xl']
}
```

### Avatar/Profile Images

```javascript
avatar: {
  width: 60,
  height: 60,
  borderRadius: 30,                         // Perfect circle
  backgroundColor: theme.colors.gray200
}
```

### Image Overlays for Text Readability

```javascript
overlay: {
  backgroundColor: 'rgba(0, 0, 0, 0.6)',   // 60% dark
  paddingHorizontal: theme.spacing.sm,
  paddingVertical: 4,
  borderRadius: theme.borderRadius.sm,
  alignSelf: 'flex-start'
}
```

## Form Patterns

### Toggle Switch

```javascript
toggle: {
  width: 50,
  height: 30,
  borderRadius: 15,
  padding: 2,
  justifyContent: 'center'
}

toggleCircle: {
  width: 26,
  height: 26,
  borderRadius: 13,
  backgroundColor: '#FFFFFF'
}
```

### Option Pills (Radio Button Alternative)

```javascript
optionsContainer: {
  flexDirection: 'row',
  flexWrap: 'wrap',
  gap: theme.spacing.sm
}

optionButton: {
  paddingHorizontal: theme.spacing.md,
  paddingVertical: theme.spacing.sm,
  borderRadius: 20,                         // Pill shape
  borderWidth: 1,
  borderColor: theme.colors.border,
  backgroundColor: theme.colors.screen.secondary
}

optionButtonActive: {
  backgroundColor: theme.colors.primary,
  borderColor: theme.colors.primary
}
```

### Photo Upload Button

```javascript
addPhotoButton: {
  height: 120,
  borderRadius: 12,
  borderWidth: 2,
  borderColor: theme.colors.border,
  borderStyle: 'dashed',
  backgroundColor: theme.colors.screen.secondary,
  alignItems: 'center',
  justifyContent: 'center'
}
```

## Best Practices

### 1. Spacing Guidelines
- Use **base (16px)** for default padding/margins
- Use **lg (20px)** for screen horizontal padding
- Use **xl (24px)** for section spacing
- Leave **120px** bottom padding for floating tab bar
- Use **8px** gap between related elements

### 2. Color Usage
- **Primary color** for primary actions, active states, accents
- **White** for cards and surfaces
- **Gray50** for screen backgrounds
- **Gray100** for input backgrounds
- **Gray500** for icons and placeholders
- **Gray600-900** for text hierarchy

### 3. Border Radius
- **Cards**: 15-20px (xl to 2xl)
- **Buttons**: 10px for rectangular, full for pills
- **Inputs**: 15px (xl)
- **Avatars/Icons**: full (perfect circle)
- **Badges**: full (pill shape)

### 4. Shadows
- Use **subtle shadows** (0.1 opacity) for depth
- Apply **stronger shadows** (0.2 opacity) only to floating elements
- Always use **vertical offset only** (no horizontal)
- Avoid harsh, dark shadows

### 5. Touch Targets
- Minimum **40x40px** for all touchable elements
- Use **44x44px** for primary actions
- Add **8-12px** spacing between touch targets

### 6. Typography Hierarchy
- **Titles**: Bold, 24-28px
- **Section headings**: SemiBold, 18-20px
- **Body text**: Normal-Medium, 16px
- **Secondary text**: Normal, 14px
- **Captions**: Normal, 12px

### 7. Loading States
- Use **opacity: 0.6** for disabled buttons
- Show **ActivityIndicator** with primary color
- Display **skeleton screens** for content loading

### 8. Error States
- Use **error color** for borders and text
- Show **clear error messages** below inputs
- Use **Ionicons** warning icons

### 9. Responsive Design
- Use **percentage widths** for flexibility
- Calculate **card widths** based on screen dimensions
- Test on multiple screen sizes (small, medium, large)

### 10. Performance
- Optimize **FlatList** with `removeClippedSubviews`
- Use **Image** with appropriate `resizeMode`
- Implement **lazy loading** for images
- Add **pull-to-refresh** for data updates

## Code Examples

### Complete Button Component

```javascript
import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';

export default function Button({
  title,
  onPress,
  variant = 'primary',  // 'primary' | 'secondary' | 'outline'
  loading = false,
  disabled = false,
  icon,
  fullWidth = false
}) {
  const { theme } = useTheme();

  const styles = {
    button: {
      backgroundColor: variant === 'primary'
        ? theme.colors.primary
        : variant === 'secondary'
        ? theme.colors.secondary
        : 'transparent',
      borderRadius: theme.borderRadius.full,
      paddingVertical: 18,
      paddingHorizontal: theme.spacing.xl,
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'row',
      gap: theme.spacing.sm,
      opacity: (loading || disabled) ? 0.6 : 1,
      borderWidth: variant === 'outline' ? 1 : 0,
      borderColor: theme.colors.primary,
      width: fullWidth ? '100%' : 'auto',
      ...theme.elevation.sm
    },
    text: {
      color: variant === 'outline'
        ? theme.colors.primary
        : theme.colors.white,
      fontSize: theme.typography.fontSize.base,
      fontWeight: theme.typography.fontWeight.semiBold
    }
  };

  return (
    <TouchableOpacity
      style={styles.button}
      onPress={onPress}
      disabled={loading || disabled}
      activeOpacity={0.7}
    >
      {loading && <ActivityIndicator color={styles.text.color} />}
      {icon && !loading && icon}
      <Text style={styles.text}>{title}</Text>
    </TouchableOpacity>
  );
}
```

### Complete Card Component

```javascript
import React from 'react';
import { View, Text, Image, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

export default function Card({
  title,
  subtitle,
  imageUri,
  onPress,
  badge,
  children
}) {
  const { theme } = useTheme();

  const styles = {
    container: {
      backgroundColor: theme.colors.white,
      borderRadius: theme.borderRadius['2xl'],
      marginBottom: theme.spacing.lg,
      overflow: 'hidden',
      ...theme.elevation.base
    },
    imageContainer: {
      position: 'relative',
      height: 200,
      backgroundColor: theme.colors.gray200
    },
    image: {
      width: '100%',
      height: '100%'
    },
    badge: {
      position: 'absolute',
      top: theme.spacing.md,
      right: theme.spacing.md,
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs,
      borderRadius: theme.borderRadius.full
    },
    badgeText: {
      color: theme.colors.white,
      fontSize: theme.typography.fontSize.xs,
      fontWeight: theme.typography.fontWeight.semiBold
    },
    content: {
      padding: theme.spacing.base
    },
    title: {
      fontSize: theme.typography.fontSize.lg,
      fontWeight: theme.typography.fontWeight.bold,
      color: theme.colors.text.primary,
      marginBottom: theme.spacing.xs
    },
    subtitle: {
      fontSize: theme.typography.fontSize.base,
      color: theme.colors.text.secondary
    }
  };

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      activeOpacity={0.95}
    >
      {imageUri && (
        <View style={styles.imageContainer}>
          <Image source={{ uri: imageUri }} style={styles.image} />
          {badge && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{badge}</Text>
            </View>
          )}
        </View>
      )}
      <View style={styles.content}>
        {title && <Text style={styles.title}>{title}</Text>}
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        {children}
      </View>
    </TouchableOpacity>
  );
}
```

## When to Use This Design System

**This design system is universal and works for ANY mobile app:**

### Perfect For:
- **E-commerce & Retail:** Product listings, shopping carts, checkout flows
- **Social Media:** Feeds, profiles, messaging, stories
- **Finance & Banking:** Account dashboards, transactions, budgeting
- **Health & Fitness:** Workout tracking, meal plans, health metrics
- **Education & Learning:** Course lists, lessons, progress tracking
- **Real Estate:** Property listings, agent profiles, search filters
- **Food & Delivery:** Restaurant menus, order tracking, reviews
- **Travel & Booking:** Hotel/flight listings, itineraries, bookings
- **Productivity:** Task lists, calendars, project management
- **Entertainment:** Media libraries, streaming, playlists
- **Service Marketplaces:** Provider listings, booking, ratings
- **News & Content:** Article feeds, categories, reading lists

### Use When You Want:
- ✅ Clean, modern, professional look
- ✅ Easy-to-read content with clear hierarchy
- ✅ Image-heavy or visual content display
- ✅ Intuitive navigation with bottom tabs
- ✅ Familiar iOS/Android patterns
- ✅ Accessible, user-friendly interfaces
- ✅ Polished, premium feel
- ✅ Consistent, reusable components

### Framework Compatibility:
- ✅ React Native (JavaScript/TypeScript)
- ✅ Flutter (Dart)
- ✅ SwiftUI (iOS native)
- ✅ Jetpack Compose (Android native)
- ✅ React Native Web
- ✅ Ionic/Capacitor
- ✅ Any mobile framework supporting custom styling

## Quick Reference Checklist

When creating a new screen:
- [ ] Set background to `theme.colors.screen.primary` (gray50)
- [ ] Use white cards with `borderRadius.xl` or `2xl`
- [ ] Apply `elevation.base` to cards
- [ ] Add `paddingBottom: 120` to scrollable content
- [ ] Use `theme.spacing.lg` for horizontal padding
- [ ] Implement rounded headers with curved bottom corners
- [ ] Make all buttons pill-shaped or rounded
- [ ] Use circular avatars and icon buttons
- [ ] Apply subtle shadows (0.1 opacity)
- [ ] Include pull-to-refresh functionality
- [ ] Add empty states with icons
- [ ] Implement loading states with opacity
- [ ] Use Ionicons for all icons
- [ ] Test touch targets (min 40x40px)
- [ ] Verify text contrast ratios

---

## Adapting This System to Your App

### Step 1: Choose Your Brand Color
Replace the primary color (`#0C125B`) with your brand color throughout the theme file.

### Step 2: Adjust Content Types
The card component works for ANY content type:
- **E-commerce:** Product images, prices, ratings
- **Social Media:** User posts, photos, engagement metrics
- **Finance:** Transaction cards, account balances
- **Health:** Workout cards, meal plans, stats
- **Education:** Course cards, lesson progress
- **Food:** Menu items, restaurant cards
- **Travel:** Hotel/flight cards, booking details

### Step 3: Customize Icons
Use appropriate icons for your app domain:
- **E-commerce:** shopping-cart, bag, heart, star
- **Social:** chatbubble, people, notifications, camera
- **Finance:** wallet, card, trending, stats
- **Health:** fitness, nutrition, heart-circle, pulse
- **Education:** book, school, trophy, checkmark

### Step 4: Adapt Navigation Labels
The floating tab bar works with any navigation structure:
```javascript
// E-commerce: Home, Shop, Cart, Profile
// Social: Feed, Discover, Messages, Profile
// Finance: Dashboard, Accounts, Transfer, More
// Health: Home, Workouts, Nutrition, Progress
// Education: Courses, Learn, Progress, Profile
```

### Step 5: Reuse Component Patterns
All components (cards, buttons, inputs, modals) work universally - just change:
- Content (text, images, data)
- Icons (match your domain)
- Colors (match your brand)
- Copy/labels (match your context)

---

## Real-World Examples Across Industries

### E-commerce App
```javascript
// Product Card
<Card
  title="Wireless Headphones"
  subtitle="$129.99"
  imageUri="product-image.jpg"
  badge="20% OFF"
/>
```

### Social Media App
```javascript
// Post Card
<Card
  title="John Doe shared a photo"
  subtitle="2 hours ago"
  imageUri="post-image.jpg"
  badge="NEW"
/>
```

### Finance App
```javascript
// Transaction Card
<Card
  title="Grocery Store"
  subtitle="-$45.20"
  imageUri="merchant-logo.jpg"
  badge="Today"
/>
```

### Health & Fitness App
```javascript
// Workout Card
<Card
  title="Morning Yoga Session"
  subtitle="45 min • 250 calories"
  imageUri="yoga-image.jpg"
  badge="COMPLETED"
/>
```

---

**This design system is completely framework-agnostic and industry-agnostic. The patterns, spacing, colors, shadows, and component structures work for ANY mobile application in ANY industry using ANY modern mobile framework.**

Use this skill to build beautiful, consistent, professional mobile UIs that users love, regardless of your app's purpose or technology stack.

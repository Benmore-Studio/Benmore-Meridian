# React Native Setup Guide - From Zero to Running on Your Phone

This guide walks you through setting up a React Native project from scratch using Expo and TypeScript, and getting it running on your actual phone.

---

## Step 1: Install Node.js

First, you need Node.js installed on your computer.

**Check if you already have it:**
```bash
node --version
```

If you see a version number (like `v18.17.0`), you're good. If not:

**Mac:**
```bash
brew install node
```

**Windows:**
Download and install from [nodejs.org](https://nodejs.org/) - grab the LTS version.

---

## Step 2: Create Your Project

Open your terminal and navigate to where you want your project:

```bash
cd ~/Documents/projects
```

Now create your new React Native app with TypeScript:

```bash
npx create-expo-app@latest MyAwesomeApp --template blank-typescript
```

This will:
- Create a new folder called `MyAwesomeApp`
- Set up a React Native project with TypeScript
- Install all the dependencies

Once it's done, go into your project:

```bash
cd MyAwesomeApp
```

---

## Step 3: Understand What You Just Created

Your project folder looks like this:

```
MyAwesomeApp/
├── App.tsx          ← This is your main app file (start here!)
├── app.json         ← App configuration (name, icon, splash screen)
├── package.json     ← Your dependencies
├── tsconfig.json    ← TypeScript configuration
├── assets/          ← Images, fonts, etc.
└── node_modules/    ← Installed packages (don't touch this)
```

Open `App.tsx` - this is where your app starts:

```typescript
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <View style={styles.container}>
      <Text>Open up App.tsx to start working on your app!</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
```

---

## Step 4: Set Up Your Phone

### Download Expo Go

On your phone, download the **Expo Go** app:
- **iPhone**: Search "Expo Go" in the App Store
- **Android**: Search "Expo Go" in the Google Play Store

This app lets you run your React Native app on your phone without needing to build it.

### Make Sure You're on the Same WiFi

Your computer and phone **must be on the same WiFi network**. This is how they talk to each other.

---

## Step 5: Run Your App

In your terminal (make sure you're in your project folder):

```bash
npx expo start
```

You'll see something like this:

```
Metro waiting on exp://192.168.1.100:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

› Using Expo Go
› Press s │ switch to development build
› Press a │ open Android
› Press i │ open iOS simulator
› Press w │ open web

› Press j │ open debugger
› Press r │ reload app
› Press m │ toggle menu
› Press o │ open project code in your editor

› Press ? │ show all commands
```

### On iPhone:
1. Open your **Camera app**
2. Point it at the QR code in your terminal
3. Tap the notification that pops up
4. It'll open in Expo Go

### On Android:
1. Open the **Expo Go app**
2. Tap "Scan QR Code"
3. Scan the QR code in your terminal

Your app should now be running on your phone!

---

## Step 6: Make Changes and See Them Live

The cool thing about React Native with Expo is **hot reloading**. When you save a file, your app updates automatically.

Try it:

1. Open `App.tsx` in your code editor (VS Code recommended)
2. Change the text:

```typescript
<Text>Hello World! This is my first app!</Text>
```

3. Save the file (Cmd+S or Ctrl+S)
4. Look at your phone - it updates automatically!

---

## Troubleshooting

### "Can't connect to Metro bundler"

**Try tunnel mode** - this works even if your WiFi is being weird:

```bash
npx expo start --tunnel
```

It'll ask you to install `@expo/ngrok` - say yes. Then scan the new QR code.

### App is stuck loading

1. Shake your phone to open the developer menu
2. Tap "Reload"

Or in your terminal, press `r` to reload.

### QR code won't scan (iPhone)

Make sure you're using the **Camera app**, not Expo Go. The Camera app detects the QR code and opens Expo Go automatically.

### "Network response timed out"

Your phone and computer aren't talking. Check:
- Same WiFi network?
- Try `npx expo start --tunnel`
- Restart the Expo server (Ctrl+C, then `npx expo start` again)

### Metro bundler crashes

Clear the cache and restart:

```bash
npx expo start --clear
```

---

## Running on Simulators (Optional)

If you want to test on your computer instead of your phone:

### iOS Simulator (Mac only)

1. Install Xcode from the App Store (it's big, like 12GB)
2. Open Xcode once to accept the license
3. In your terminal with Expo running, press `i`

### Android Emulator

1. Install [Android Studio](https://developer.android.com/studio)
2. Open Android Studio > More Actions > Virtual Device Manager
3. Create a new virtual device (pick any phone, like Pixel 7)
4. Download a system image and create the emulator
5. Start the emulator
6. In your terminal with Expo running, press `a`

---

## Next Steps

Now that your app is running, here are common things you'll want to add:

### Navigation (moving between screens)

```bash
npx expo install @react-navigation/native @react-navigation/stack react-native-screens react-native-safe-area-context react-native-gesture-handler
```

### Icons

Icons are already included with Expo:

```typescript
import { Ionicons } from '@expo/vector-icons';

<Ionicons name="home" size={24} color="black" />
```

### Making API calls

```bash
npm install axios
```

### Storing data locally

```bash
npx expo install @react-native-async-storage/async-storage
```

---

## Using Claude Code for UI Design

When you're using Claude Code to help you design and build your mobile app, the UI can sometimes look "AI-generated" - generic, bland, or inconsistent. To avoid this, you can use these Claude Code skills to get professional, polished designs.

### Available Skills

Get them from: **https://github.com/ouujay/claudeskills**

#### 1. Minimalist UI Design
Use this for the **overall look of your app** - cards, buttons, typography, forms.

Features:
- Light typography (font-weight 300 for headers) - clean, modern look
- Black buttons with white text
- White cards with subtle gray borders (no heavy shadows)
- No gradients - just clean, flat design
- Professional, not "AI-generated" looking

#### 2. Modern Floating UI Design
Use this for the **bottom navigation bar** - gives you that premium iOS-style floating tab bar.

Features:
- Floating pill-shaped navigation bar lifted from the bottom
- Soft shadows and subtle elevation
- Active tab indicator with circular background
- Rounded corners everywhere
- Glass-morphic effects

### How to Use These Skills

When prompting Claude Code, tell it which skill to use:

```
"Design a home screen for my food delivery app. Use the minimalist-ui-design
skill for the overall styling (cards, buttons, typography) and the
modern-floating-ui-design skill for the bottom tab navigation."
```

Or reference specific patterns:

```
"Add a bottom navigation bar using the floating pill-shaped tab bar pattern
from the modern-floating-ui-design skill."
```

### Why Use These Skills?

Without guidance, AI-generated UI tends to:
- Use too many gradients and shadows
- Have inconsistent spacing and colors
- Look generic and template-like
- Mix different design styles

These skills give Claude Code specific rules to follow, resulting in consistent, professional-looking apps that don't scream "AI made this."

---

## Quick Reference

| Command | What it does |
|---------|--------------|
| `npx expo start` | Start the development server |
| `npx expo start --tunnel` | Start with tunnel (fixes network issues) |
| `npx expo start --clear` | Start with cleared cache |
| `npx expo install <package>` | Install a package (use this instead of npm for Expo packages) |
| Press `r` in terminal | Reload the app |
| Press `m` in terminal | Open dev menu |
| Press `i` in terminal | Open iOS simulator |
| Press `a` in terminal | Open Android emulator |
| Press `w` in terminal | Open web version |

---

## You're All Set!

You now have:
- ✅ A React Native project with TypeScript
- ✅ Your app running on your phone
- ✅ Hot reloading so changes appear instantly
- ✅ Claude Code skills for professional UI design

Start building by editing `App.tsx` and adding more screens!

---

## Related Guides

- [Heroku Django Deployment](01-heroku-django.md) - Backend API deployment
- [Django CI/CD Setup](03-django-cicd-setup.md) - Automated testing and deployment
- [Django Production Guide](../django/02-detailed-checklist.md) - Backend production readiness

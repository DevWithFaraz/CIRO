import { initializeApp, getApps, getApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

// Replace with your actual Firebase config
const firebaseConfig = {
  apiKey: "YOUR_WEB_API_KEY",
  authDomain: "ciro-31298.firebaseapp.com",
  projectId: "ciro-31298",
  storageBucket: "ciro-31298.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// The "Web Conflict" safeguard:
// Prevent Expo Go hot-reloading from throwing "Firebase App already exists"
let app;
if (getApps().length === 0) {
  app = initializeApp(firebaseConfig);
} else {
  app = getApp();
}

const db = getFirestore(app);

export { app, db };

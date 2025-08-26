import 'package:flutter/material.dart';
import 'screens/wardrobe_screen.dart';
import 'screens/suggestion_screen.dart';
import 'screens/upload_screen.dart';

void main() {
  runApp(const OutfitApp());
}

class OutfitApp extends StatelessWidget {
  const OutfitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Outfit Optimizer",
      theme: ThemeData(primarySwatch: Colors.deepPurple),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Outfit Optimizer")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              child: const Text("📸 Upload Clothing"),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const UploadScreen()),
                );
              },
            ),
            ElevatedButton(
              child: const Text("👕 My Wardrobe"),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const WardrobeScreen()),
                );
              },
            ),
            ElevatedButton(
              child: const Text("🎭 Outfit Suggestion"),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const SuggestionScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
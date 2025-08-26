import 'package:flutter/material.dart';
import '../services/api_service.dart';

class WardrobeScreen extends StatefulWidget {
  const WardrobeScreen({super.key});

  @override
  State<WardrobeScreen> createState() => _WardrobeScreenState();
}

class _WardrobeScreenState extends State<WardrobeScreen> {
  List<dynamic> wardrobe = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    loadWardrobe();
  }

  Future<void> loadWardrobe() async {
    try {
      var items = await ApiService.fetchWardrobe();
      setState(() {
        wardrobe = items;
        loading = false;
      });
    } catch (e) {
      setState(() => loading = false);
      debugPrint("Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("My Wardrobe")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: wardrobe.length,
              itemBuilder: (context, index) {
                var item = wardrobe[index];
                return Card(
                  margin: const EdgeInsets.all(8),
                  child: ListTile(
                    leading: Image.network(
                      "${ApiService.baseUrl}/images/${item['filename']}",
                      width: 50,
                      height: 50,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) =>
                          const Icon(Icons.broken_image),
                    ),
                    title: Text(item["label"] ?? "Unknown"),
                    subtitle:
                        Text("Color: ${item["color_hex"] ?? "#000000"}"),
                  ),
                );
              },
            ),
    );
  }
}

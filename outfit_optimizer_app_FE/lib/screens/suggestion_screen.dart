import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const backendUrl = "http://127.0.0.1:8000";

class SuggestionScreen extends StatefulWidget {
  const SuggestionScreen({super.key});

  @override
  State<SuggestionScreen> createState() => _SuggestionScreenState();
}

class _SuggestionScreenState extends State<SuggestionScreen> {
  String? suggestion;
  List<String> usedImages = [];
  String event = "office";
  bool loading = false;

  Future<void> fetchSuggestion() async {
    setState(() {
      loading = true;
      suggestion = null;
      usedImages.clear();
    });

    try {
      final response =
          await http.get(Uri.parse("$backendUrl/suggest?event=$event"));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Debug: Print the response to see what we're getting
        print("API Response: $data");
        
        // Extract text advice
        suggestion = data["advice"];
        
        // Get used_items directly from the response (these should be actual filenames)
        if (data["used_items"] != null && data["used_items"] is List) {
          usedImages = List<String>.from(data["used_items"]);
          print("Used images from API: $usedImages");
        } else {
          // Fallback: try to parse filenames from the advice text with a more flexible regex
          // This regex looks for common image file patterns
          final regex = RegExp(r"(\S+\.(jpg|jpeg|png|gif|webp))", caseSensitive: false);
          final matches = regex.allMatches(suggestion!);
          usedImages = matches.map((m) => m.group(1)!).toList();
          print("Used images from regex fallback: $usedImages");
        }
        
        print("Final used images: $usedImages");
      } else {
        suggestion = "Failed to fetch suggestion (Status: ${response.statusCode})";
        print("HTTP Error: ${response.statusCode} - ${response.body}");
      }
    } catch (e) {
      suggestion = "Error: $e";
      print("Exception: $e");
    }

    setState(() {
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Outfit Suggestion")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButton<String>(
              value: event,
              items: const [
                DropdownMenuItem(value: "office", child: Text("Office")),
                DropdownMenuItem(value: "casual", child: Text("Casual")),
                DropdownMenuItem(value: "party", child: Text("Party")),
              ],
              onChanged: (val) => setState(() => event = val!),
            ),
            const SizedBox(height: 10),
            ElevatedButton(
              onPressed: fetchSuggestion,
              child: const Text("Get Outfit Suggestion"),
            ),
            const SizedBox(height: 16),
            if (loading)
              const Center(child: CircularProgressIndicator())
            else if (suggestion != null)
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        suggestion!,
                        style: const TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 20),
                      if (usedImages.isNotEmpty) ...[
                        const Text(
                          "Suggested Items:",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          children: usedImages.map((file) {
                            // Debug: Print each image URL being requested
                            final imageUrl = "$backendUrl/images/$file";
                            print("Requesting image: $imageUrl");
                            
                            return Column(
                              children: [
                                Container(
                                  decoration: BoxDecoration(
                                    border: Border.all(color: Colors.grey.shade300),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(8),
                                    child: Image.network(
                                      imageUrl,
                                      width: 100,
                                      height: 100,
                                      fit: BoxFit.cover,
                                      loadingBuilder: (context, child, loadingProgress) {
                                        if (loadingProgress == null) return child;
                                        return Container(
                                          width: 100,
                                          height: 100,
                                          color: Colors.grey.shade100,
                                          child: Center(
                                            child: CircularProgressIndicator(
                                              value: loadingProgress.expectedTotalBytes != null
                                                  ? loadingProgress.cumulativeBytesLoaded /
                                                      loadingProgress.expectedTotalBytes!
                                                  : null,
                                            ),
                                          ),
                                        );
                                      },
                                      errorBuilder: (context, error, stackTrace) {
                                        // Debug: Print the error
                                        print("Image load error for $file: $error");
                                        return Container(
                                          width: 100,
                                          height: 100,
                                          color: Colors.grey.shade200,
                                          child: Column(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              const Icon(
                                                Icons.image_not_supported,
                                                color: Colors.grey,
                                                size: 30,
                                              ),
                                              const SizedBox(height: 4),
                                              Text(
                                                "Error",
                                                style: TextStyle(
                                                  fontSize: 8,
                                                  color: Colors.grey[600],
                                                ),
                                              ),
                                            ],
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 4),
                                SizedBox(
                                  width: 100,
                                  child: Text(
                                    file,
                                    style: const TextStyle(fontSize: 9),
                                    textAlign: TextAlign.center,
                                    overflow: TextOverflow.ellipsis,
                                    maxLines: 2,
                                  ),
                                ),
                              ],
                            );
                          }).toList(),
                        ),
                      ] else ...[
                        const Text(
                          "No specific items mentioned in the suggestion.",
                          style: TextStyle(
                            fontSize: 14,
                            fontStyle: FontStyle.italic,
                            color: Colors.grey,
                          ),
                        ),
                      ]
                    ],
                  ),
                ),
              )
          ],
        ),
      ),
    );
  }
}
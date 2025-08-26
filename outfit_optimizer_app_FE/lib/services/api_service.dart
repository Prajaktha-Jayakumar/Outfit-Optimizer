import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://127.0.0.1:8000";

  static Future<Map<String, dynamic>> uploadClothing(File image) async {
    var request = http.MultipartRequest("POST", Uri.parse("$baseUrl/upload/"));
    request.files.add(await http.MultipartFile.fromPath("file", image.path));
    var response = await request.send();

    if (response.statusCode == 200) {
      var body = await response.stream.bytesToString();
      return jsonDecode(body);
    } else {
      throw Exception("Upload failed: ${response.statusCode}");
    }
  }

  static Future<Map<String, dynamic>> suggestOutfit(String event) async {
    var url = Uri.parse("$baseUrl/suggest?event=$event");
    var response = await http.get(url);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Suggestion failed: ${response.statusCode}");
    }
  }

  static Future<List<dynamic>> fetchWardrobe() async {
    var response = await http.get(Uri.parse("$baseUrl/wardrobe"));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Failed to fetch wardrobe");
    }
  }
}

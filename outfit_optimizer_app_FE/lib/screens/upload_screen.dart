import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  File? _image;
  Uint8List? _webImage;
  String _result = "";
  bool _isLoading = false;

  Future<void> _pickAndUploadImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile == null) return;

    if (kIsWeb) {
      final bytes = await pickedFile.readAsBytes();
      setState(() {
        _webImage = bytes;
        _image = null;
      });
    } else {
      setState(() {
        _image = File(pickedFile.path);
        _webImage = null;
      });
    }

    setState(() {
      _isLoading = true;
      _result = "Analyzing your outfit...";
    });

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('http://127.0.0.1:8000/upload/'),
      );

      if (kIsWeb) {
        request.files.add(http.MultipartFile.fromBytes(
          'file',
          await pickedFile.readAsBytes(),
          filename: pickedFile.name,
        ));
      } else {
        request.files.add(await http.MultipartFile.fromPath('file', pickedFile.path));
      }

      final response = await request.send();

      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        final jsonResponse = json.decode(respStr);

        final filename = jsonResponse['filename'] ?? 'Unknown item';
        final label = jsonResponse['label'] ?? 'Unknown type';
        final colorInfo = jsonResponse['color'] ?? [];

        String colorText = '';
        if (colorInfo.length >= 2) {
          colorText = 'Color: ${colorInfo[1]} (RGB: ${colorInfo[0]})';
        }

        setState(() {
          _result = '''
📸 Uploaded: $filename
🏷️ Detected: $label
🎨 $colorText
💡 Fashion Tip: This ${label.toLowerCase()} would look great paired with complementary colors and matching accessories!
✨ Try adding some neutral pieces or contrasting colors to complete your look.
          '''.trim();
        });
      } else {
        setState(() {
          _result = "Upload failed with status: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _result = "Error: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Widget _buildImageWidget() {
    if (kIsWeb && _webImage != null) {
      return Image.memory(_webImage!, height: 200, fit: BoxFit.cover);
    } else if (!kIsWeb && _image != null) {
      return Image.file(_image!, height: 200, fit: BoxFit.cover);
    }
    return const SizedBox.shrink();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Upload Clothing")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(child: _buildImageWidget()),
            const SizedBox(height: 20),
            Center(
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _pickAndUploadImage,
                icon: _isLoading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.upload),
                label: Text(_isLoading ? "Analyzing..." : "Upload Clothing Image"),
              ),
            ),
            const SizedBox(height: 20),
            if (_result.isNotEmpty)
              Expanded(
                child: SingleChildScrollView(
                  child: Text(_result, style: const TextStyle(fontSize: 14, height: 1.5)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

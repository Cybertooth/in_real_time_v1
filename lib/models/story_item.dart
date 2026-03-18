import 'package:cloud_firestore/cloud_firestore.dart';

abstract class StoryItem {
  final DateTime unlockTimestamp;

  StoryItem({required this.unlockTimestamp});

  bool get isLocked => DateTime.now().isBefore(unlockTimestamp);
}

class Journal extends StoryItem {
  final String title;
  final String body;

  Journal({
    required this.title,
    required this.body,
    required super.unlockTimestamp,
  });

  factory Journal.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return Journal(
      title: data['title'] ?? '',
      body: data['body'] ?? '',
      unlockTimestamp: (data['unlockTimestamp'] as Timestamp).toDate(),
    );
  }
}

class Chat extends StoryItem {
  final String senderId;
  final String text;
  final bool isProtagonist;

  Chat({
    required this.senderId,
    required this.text,
    required this.isProtagonist,
    required super.unlockTimestamp,
  });

  factory Chat.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return Chat(
      senderId: data['senderId'] ?? '',
      text: data['text'] ?? '',
      isProtagonist: data['isProtagonist'] ?? false,
      unlockTimestamp: (data['unlockTimestamp'] as Timestamp).toDate(),
    );
  }
}

class Email extends StoryItem {
  final String sender;
  final String subject;
  final String body;

  Email({
    required this.sender,
    required this.subject,
    required this.body,
    required super.unlockTimestamp,
  });

  factory Email.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return Email(
      sender: data['sender'] ?? '',
      subject: data['subject'] ?? '',
      body: data['body'] ?? '',
      unlockTimestamp: (data['unlockTimestamp'] as Timestamp).toDate(),
    );
  }
}

class Receipt extends StoryItem {
  final String merchantName;
  final double amount;
  final String description;

  Receipt({
    required this.merchantName,
    required this.amount,
    required this.description,
    required super.unlockTimestamp,
  });

  factory Receipt.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return Receipt(
      merchantName: data['merchantName'] ?? '',
      amount: (data['amount'] as num).toDouble(),
      description: data['description'] ?? '',
      unlockTimestamp: (data['unlockTimestamp'] as Timestamp).toDate(),
    );
  }
}

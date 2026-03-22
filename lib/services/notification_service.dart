import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import '../models/story_item.dart';

final notificationServiceProvider = Provider<NotificationService>((ref) {
  return NotificationService();
});

class NotificationService {
  final _notificationsPlugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    tz.initializeTimeZones();
    
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const initSettings = InitializationSettings(
      android: androidInit,
      iOS: iosInit,
    );

    
    await _notificationsPlugin.initialize(
      settings: initSettings,
      onDidReceiveNotificationResponse: (NotificationResponse details) {
        // Handle notification tap
      },
    );
    _initialized = true;
    
  }

  Future<void> scheduleItemUnlock(StoryItem item) async {
    
    if (!_initialized) await init();
    if (item.unlockTimestamp.isBefore(DateTime.now())) return;

    final id = item.id.hashCode;
    
    try {
      await _notificationsPlugin.zonedSchedule(
        id: id,
        title: 'Incoming Intercept',
        body: 'New ${item.contentType.toUpperCase()} has been decrypted. Tap to read.',
        scheduledDate: tz.TZDateTime.from(item.unlockTimestamp, tz.local),
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'in_real_time_channel',
            'Story Drops',
            channelDescription: 'Notifications for newly unlocked story items',
            importance: Importance.max,
            priority: Priority.high,
          ),
          iOS: DarwinNotificationDetails(),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );
    } catch (e) {
      print('Failed to schedule notification: $e');
    }
    
  }
}

from notification.serializers import NotificationSerializer

def get_notification(message,event,sender_id,receiver_id,subject,email_id,email_message,role,iu_id):
    data={
        "event":event.id,
        "sender":sender_id,
        "receiver":receiver_id,
        "subject":subject,
        "message":message,
        "email_id":email_id,
        "email_message":email_message,
        "role":role,
        "iu_id":iu_id,
        "created_by":sender_id
    }
    serializer=NotificationSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors
    serializer.save()
    return 1
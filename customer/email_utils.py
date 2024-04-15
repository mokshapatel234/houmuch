from django.conf import settings


def vendor_cancellation_data(booking, guest, refund_amount, cancellation_charge_percentage=0,
                             transfer_amount=0, cancellation_charge_amount=0, commission_percent=0, is_cancel=False):
    return {"subject": f"Booking Cancellation: Check-in on {booking.check_in_date.date()}",
            "email": booking.property.owner.email,
            "template": "vendor_cancellation.html",
            "context": {'guest_name': booking.customer.first_name + ' ' + booking.customer.last_name,
                        'guest_email': booking.customer.email,
                        'guest_number': booking.customer.phone_number,
                        'booking_id': booking.id,
                        'property_name': booking.property.owner.hotel_name,
                        'room_name': booking.rooms.room_name,
                        'room_type': booking.rooms.room_type,
                        'amount': booking.amount,
                        'num_of_rooms': booking.num_of_rooms,
                        'num_of_adults': guest.no_of_adults,
                        'num_of_children': guest.no_of_adults,
                        'check_in_date': booking.check_in_date.date(),
                        'cancel_reason': booking.cancel_reason,
                        'cancellation_percents': cancellation_charge_percentage,
                        'refund_amount': refund_amount,
                        'transfer_amount': transfer_amount,
                        'non_refunded_amount': cancellation_charge_amount,
                        'commission_percent': commission_percent,
                        'is_cancel': is_cancel}}


def customer_cancellation_data(booking, guest, cancellation_charge_percentage, refund_amount, is_cancel=False):
    return {"subject": f"Booking Cancellation: Check-in on {booking.check_in_date.date()}",
            "email": booking.customer.email,
            "template": "customer_cancellation.html",
            "context": {'customer_name': booking.customer.first_name + ' ' + booking.customer.last_name,
                        'property_name': booking.property.owner.hotel_name,
                        'property_email': booking.property.owner.email,
                        'property_number': booking.property.owner.phone_number,
                        'address': booking.property.owner.address,
                        'room_name': booking.rooms.room_name,
                        'room_type': booking.rooms.room_type,
                        'amount': booking.amount,
                        'num_of_rooms': booking.num_of_rooms,
                        'num_of_adults': guest.no_of_adults,
                        'num_of_children': guest.no_of_adults,
                        'check_in_date': booking.check_in_date.date(),
                        'check_out_date': booking.check_out_date.date(),
                        'cancel_reason': booking.cancel_reason,
                        'cancellation_percents': cancellation_charge_percentage,
                        'refund_amount': refund_amount,
                        'is_cancel': is_cancel}}


def vendor_booking_confirmation_data(booking, guest):
    return {"subject": f"Booking Confirmation: Check-in on {booking.check_in_date.date()}",
            "email": booking.property.owner.email,
            "template": "vendor_confirm_booking.html",
            "context": {'guest_name': booking.customer.first_name + ' ' + booking.customer.last_name,
                        'property_name': booking.property.owner.hotel_name,
                        'guest_email': booking.customer.email,
                        'guest_number': booking.customer.phone_number,
                        'room_name': booking.rooms.room_name,
                        'room_type': booking.rooms.room_type,
                        'amount': booking.amount,
                        'num_of_rooms': booking.num_of_rooms,
                        'num_of_adults': guest.no_of_adults,
                        'num_of_children': guest.no_of_adults,
                        'check_in_date': booking.check_in_date.date(),
                        'check_out_date': booking.check_out_date.date()}}


def customer_booking_confirmation_data(booking, guest, policies):
    return {"subject": f"Booking Confirmation: Check-in on {booking.check_in_date.date()}",
            "email": booking.customer.email,
            "template": "customer_confirm_booking.html",
            "context": {'customer_name': booking.customer.first_name + ' ' + booking.customer.last_name,
                        'property_name': booking.property.owner.hotel_name,
                        'property_email': booking.property.owner.email,
                        'property_number': booking.property.owner.phone_number,
                        'address': booking.property.owner.address,
                        'property_id': booking.property.id,
                        'room_name': booking.rooms.room_name,
                        'room_type': booking.rooms.room_type,
                        'floor': booking.rooms.floor,
                        'amount': booking.amount,
                        'num_of_adults': guest.no_of_adults,
                        'num_of_children': guest.no_of_adults,
                        'check_in_date': booking.check_in_date.date(),
                        'check_out_date': booking.check_out_date.date(),
                        'policies': policies}}


def customer_welcome_data(request, email):
    return {"subject": f'Welcome {request.user.first_name}',
            "email": email,
            "template": "welcome_customer.html",
            "context": {'first_name': request.user.first_name, 'last_name': request.user.last_name}}


def vendor_welcome_data(instance):
    return {"subject": f'Welcome {instance.hotel_name}',
            "email": instance.email,
            "template": "welcome_email.html",
            "context": {'hotel_name': instance.hotel_name}}


def vendor_otp_data(email, otp):
    return {"subject": 'OTP Verification',
            "email": email,
            "template": "otp.html",
            "context": {'otp': otp}}


def vendor_property_verification_data(admin_email, instance):
    return {"subject": 'Property Verification',
            "email": admin_email,
            "template": "property_verify.html",
            "context": {
                'property_name': instance.owner.hotel_name,
                'parent_hotel_group': instance.parent_hotel_group,
                'address': instance.owner.address,
                'property_id': instance.id,
                'backend_url': settings.BACKEND_URL}}


def vendor_room_verification_data(admin_email, instance, property_instance):
    return {"subject": 'Room Verification',
            "email": admin_email,
            "template": "room_verify.html",
            "context": {
                'room_name': instance.room_name,
                'property_name': property_instance.owner.hotel_name,
                'floor': instance.floor,
                'address': property_instance.owner.address,
                'room_id': instance.id,
                'backend_url': settings.BACKEND_URL}}

from django.utils.translation import gettext as _

SUCCESS_MESSAGE = _('Operation successful.')
FAILURE_MESSAGE = _('Operation failed.')
REGISTRATION_SUCCESS_MESSAGE = _('Congratulations, you are registered.')
LOGIN_SUCCESS_MESSAGE = _('Congratulations, you are logged in.')
OWNER_NOT_VERIFIED_MESSAGE = _('Owner not verified by admin.')
NOT_REGISTERED_MESSAGE = _('You are not registered.')
PHONE_REQUIRED_MESSAGE = _('Phone number is required for registration.')
PHONE_ALREADY_PRESENT_MESSAGE = _('Phone number is already present.')
EXCEPTION_MESSAGE = _('Something went wrong.')
INVALID_TOKEN_MESSAGE = _('Token is invalid.')
TOKEN_REQUIRED_MESSAGE = _('Token is required.')
DEVICE_ID_ERROR_MESSAGE = _('Device id does not matched.')
CUSTOMER_NOT_FOUND_MESSAGE = _('Customer not found.')
OWNER_NOT_FOUND_MESSAGE = _('Owner not found.')
PROFILE_MESSAGE = _('Profile retrieved successfully.')
PROFILE_UPDATE_MESSAGE = _('Profile updated suceessfully.')
PROFILE_ERROR_MESSAGE = _('Invalid data provided.')
EMAIL_ALREADY_PRESENT_MESSAGE = _('Email is already present.')
PROPERTY_CREATION_MESSAGE = _('Property added successfully.')
DATA_RETRIEVAL_MESSAGE = _('Data retrieved successfully.')
DATA_CREATE_MESSAGE = _("Data created successfully.")
DATA_UPDATE_MESSAGE = _("Data updated successfully.")
DATA_DELETE_MESSAGE = _("Data deleted successfully.")
OBJECT_NOT_FOUND_MESSAGE = _("Object not found.")
ENTITY_ERROR_MESSAGE = _("Fields are required.")
SENT_OTP_MESSAGE = _("OTP sent to requested email")
OTP_VERIFICATION_SUCCESS_MESSAGE = _("OTP verification successful.")
OTP_VERIFICATION_INVALID_MESSAGE = _("Invalid OTP.")
INVALID_INPUT_MESSAGE = _('Invalid input data.')
FAILED_PRESIGNED_RESPONSE = _('Failed to generate presigned URL')
PAYMENT_MISSING_INFO_MESSAGE = _('Room IDs, property ID, check_in_date, check_out_date and amount are required in request data.')
PAYMENT_ERROR_MESSAGE = _('Room IDs already exist in session.')
PAYMENT_SUCCESS_MESSAGE = _('Payment success. Booking created.')
ROOM_IDS_MISSING_MESSAGE = _("One or more room IDs are invalid")
PAYMEMT_MISSING_PROPERTY_OR_CUSTOMER = _("Property or Customer does not exist")
PAYMENT_SUCCESS_MESSAGE = _('Room IDs set in session successfully.')
ROOM_IDS_MISSING_MESSAGE = _('Room IDs are missing.')
ORDER_SUFFICIENT_MESSAGE = _('Sufficient rooms available.')
BOOKED_INFO_MESSAGE = _("{total_booked} room(s) already booked.")
SESSION_INFO_MESSAGE = _("{session_rooms_booked} room(s) currently locked/reserved in session.")
AVAILABILITY_INFO_MESSAGE = _("{adjusted_availability} room(s) available.")
REQUIREMENT_INFO_MESSAGE = _("{additional_rooms_needed} more required.")
PLAN_EXPIRY_MESSAGE = _("Plan has expired")
ACCOUNT_ERROR_MESSAGE = _("An account already exists for this owner.")
ACCOUNT_PRODUCT_UPDATION_FAIL_MESSAGE = _("Failed to update product and bank details in Razorpay.")
CREATE_PRODUCT_FAIL_MESSAGE = _("Failed to create product in Razorpay.")
ACCOUNT_CREATE_FAIL_MESSAGE = _("Failed to create account in Razorpay.")
OWNER_ID_NOT_PROVIDED_MESSAGE = _("Owner ID not provided in the query parameters.")
PROVIDER_NOT_FOUND_MESSAGE = _("Account not found for the provided owner ID.")
ACCOUNT_DETAIL_UPDATE_MESSAGE = _("Account details updated successfully")
BANKING_DETAIL_NOT_EXIST_MESSAGE = _("Owner banking detail does not exist.")
ROOM_NOT_AVAILABLE_MESSAGE = _("rooms are not available as per you requirements.")
PRODUCT_AND_BANK_DETAIL_SUCESS_MESSAGE = _("Product and bank details updated successfully.")
ORDER_ERROR_MESSAGE = _("Failed to update order.")
REFUND_SUCCESFULL_MESSAGE = _("Refund processed successfully.")
REFUND_ERROR_MESSAGE = _("Failed to process refund.")
DIRECT_TRANSFER_ERROR_MESSAGE = _("Failed to process direct transfer.")

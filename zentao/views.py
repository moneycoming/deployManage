import json

from django.http import JsonResponse


def __get_response_json_dict(data, err_code=0, message="Success"):
    ret = {
        'err_code': err_code,
        'message': message,
        'data': data
    }
    return ret


def get_sum(request):
    received_data = json.loads(request.body)
    var1 = received_data['var1']
    var2 = received_data['var2']

    sum = var1 + var2

    response_data = {"sum": sum}

    return JsonResponse(
        __get_response_json_dict(data=response_data)
    )

def __get_productBugPercent_response_json_dict(result, productID, bugStatus, bugLevel, message):
    ret = {
        'result': result,
        'productID': productID,
        'bugStatus': bugStatus,
        'bugLevel': bugLevel,
        'message': message
    }
    return ret


def __get_productTaskPercent_response_json_dict(result, productID, count, actualQuantity, targetQuantity, message):
    ret = {
        'result': result,
        'productID': productID,
        'count': count,
        'actualQuantity': actualQuantity,
        'targetQuantity': targetQuantity,
        'message': message
    }

    return ret


def __get_productTaskStatusPercent_response_json_dict(result, productID, count, wait, doing, done, message):
    ret = {
        'result': result,
        'productID': productID,
        'count': count,
        'wait': wait,
        'doing': doing,
        'done': done,
        'message': message
    }

    return ret


def __get_productScorePercent_response_json_dict(result, productID, now, total, message):
    ret = {
        'result': result,
        'productID': productID,
        'now': now,
        'all': total,
        'message': message
    }

    return ret

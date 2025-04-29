from django.shortcuts import render
import requests
from django.http import JsonResponse
import json
# Create your views here.

def get_all_data(records_all, current_page):
    url = 'http://mgn.delink.top:8005/client/get-client-list'
    headers = {
        'Content-Type': 'application/json'
    }
    post_data = {
        "pageNum": current_page,
        "accessKey": "5AD",
        "pageSize": 1000,
        "pointStatus": "M100",
        "productLine": ""
    }
    try:
        response = requests.post(url, json=post_data, headers=headers)
        data = response.json()
        records = data.get('records', [])
        total = data.get('total', 0)
        current = data.get('current', 1)
        pages = data.get('pages', 1)
        
        records_all.extend(records)
        
        if pages > current_page:
            return get_all_data(records_all, current_page + 1)

        return {
            'records': records_all,
            'total': total,
            'current': current,
            'pages': pages
        }
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return {
            'records': records_all,
            'total': 0,
            'current': current_page,
            'pages': 1
        }

def get_jss_data(request):
    records_all = []
    data = get_all_data(records_all, 1)
    # 倒序
    data['records'].reverse()
    return render(request, 'jssp/index.html', {'data': data})


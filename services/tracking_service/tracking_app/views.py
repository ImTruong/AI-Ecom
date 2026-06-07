from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SearchHistory, ProductView, CartAction, PurchaseAction
import json
from .application.use_cases import TrackingUseCases
from .domain.exceptions import TrackingValidationError
from .infrastructure.repositories import DjangoTrackingRepository
from .presentation.serializers import tracking_event_to_dict


tracking_use_cases = TrackingUseCases(DjangoTrackingRepository())

class LogSearchView(APIView):
    def post(self, request):
        try:
            query = request.data.get('query')
            customer_id = request.data.get('customer_id')
            
            if not query:
                return Response({'success': False, 'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            SearchHistory.objects.create(
                customer_id=customer_id,
                query=query
            )
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogProductView(APIView):
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            product_type = request.data.get('product_type')
            customer_id = request.data.get('customer_id')
            
            # Safe convert customer_id to int
            try:
                if customer_id and str(customer_id).isdigit():
                    customer_id = int(customer_id)
                else:
                    customer_id = None
            except:
                customer_id = None
            
            if not product_id or not product_type:
                return Response({'success': False, 'error': 'Product ID and Type are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            ProductView.objects.create(
                customer_id=customer_id,
                product_id=product_id,
                product_type=product_type
            )
            event = tracking_use_cases.record_event({
                **request.data,
                'event_type': 'ClickProduct',
                'user_id': customer_id,
                'product_id': product_id,
            })
            return Response({'success': True, 'event': tracking_event_to_dict(event)}, status=status.HTTP_201_CREATED)
        except TrackingValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogCartActionView(APIView):
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            product_type = request.data.get('product_type')
            action_type = request.data.get('action_type', 'add')
            customer_id = request.data.get('customer_id')
            quantity = request.data.get('quantity', 1)
            price = request.data.get('price')
            
            # Safe convert customer_id to int
            try:
                if customer_id and str(customer_id).isdigit():
                    customer_id = int(customer_id)
                else:
                    customer_id = None
            except:
                customer_id = None

            if not product_id or not product_type:
                return Response({'success': False, 'error': 'Product ID and Type are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure price is a decimal or None
            if price == '': price = None
                
            CartAction.objects.create(
                customer_id=customer_id,
                product_id=product_id,
                product_type=product_type,
                action_type=action_type,
                quantity=quantity,
                price=price
            )
            event = tracking_use_cases.record_event({
                **request.data,
                'event_type': 'AddToCart',
                'user_id': customer_id,
                'product_id': product_id,
            })
            return Response({'success': True, 'event': tracking_event_to_dict(event)}, status=status.HTTP_201_CREATED)
        except TrackingValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogPurchaseView(APIView):
    def post(self, request):
        try:
            customer_id = request.data.get('customer_id')
            
            # Safe convert customer_id to int
            try:
                if customer_id and str(customer_id).isdigit():
                    customer_id = int(customer_id)
                else:
                    customer_id = None
            except:
                customer_id = None
                
            items = request.data.get('items', [])
            order_id = request.data.get('order_id')
            
            for item in items:
                PurchaseAction.objects.create(
                    customer_id=customer_id,
                    product_id=item['product_id'],
                    product_type=item['product_type'],
                    order_id=order_id,
                    price=item['price'],
                    quantity=item['quantity']
                )
                tracking_use_cases.record_event({
                    'event_type': 'PlaceOrder',
                    'user_id': customer_id,
                    'product_id': item['product_id'],
                    'product_variant_id': item.get('variant_id'),
                    'metadata': {
                        'order_id': order_id,
                        'product_type': item.get('product_type'),
                        'price': item.get('price'),
                        'quantity': item.get('quantity'),
                    },
                })
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        except TrackingValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogTrackingEventView(APIView):
    def post(self, request):
        try:
            event = tracking_use_cases.record_event(request.data)
            return Response({'success': True, 'data': tracking_event_to_dict(event)}, status=status.HTTP_201_CREATED)
        except TrackingValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetStatsView(APIView):
    def get(self, request):
        stats = {
            'total_searches': SearchHistory.objects.count(),
            'total_views': ProductView.objects.count(),
            'total_cart_actions': CartAction.objects.count(),
            'recent_searches': [s.to_dict() for s in SearchHistory.objects.all().order_by('-timestamp')[:5]],
            'recent_views': [v.to_dict() for v in ProductView.objects.all().order_by('-timestamp')[:5]],
            'recent_cart_actions': [c.to_dict() for c in CartAction.objects.all().order_by('-timestamp')[:5]]
        }
        return Response({'success': True, 'data': stats})

class GetUserHistoryView(APIView):
    def get(self, request, customer_id):
        views = ProductView.objects.filter(customer_id=customer_id).order_by('-timestamp')[:20]
        carts = CartAction.objects.filter(customer_id=customer_id, action_type='add').order_by('-timestamp')[:20]
        purchases = PurchaseAction.objects.filter(customer_id=customer_id).order_by('-timestamp')[:20]
        searches = SearchHistory.objects.filter(customer_id=customer_id).order_by('-timestamp')[:20]
        
        return Response({
            'success': True,
            'data': {
                'views': [v.to_dict() for v in views],
                'carts': [c.to_dict() for c in carts],
                'purchases': [p.to_dict() for p in purchases],
                'searches': [s.to_dict() for s in searches]
            }
        })

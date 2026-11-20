"""
Handler: Stock Decreased (Payments API)
SPDX-License-Identifier: LGPL-3.0-or-later
"""
from typing import Dict, Any
from event_management.base_handler import EventHandler


class StockDecreasedHandler(EventHandler):
    """Receives StockDecreased events published by the Store Manager"""

    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockDecreased"

    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        # NOTE: la transaction de paiement est créée par le StockDecreasedHandler du Store Manager (appel synchrone,
        # puis patron Outbox à l'activité 6). Créer le paiement ici aussi produirait un doublon pour chaque commande.
        # Pour publier un résultat : OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)
        self.logger.debug(f"StockDecreased reçu pour la commande {event_data.get('order_id')} "
                          f"(total_amount={event_data.get('total_amount')})")

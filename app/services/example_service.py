"""Пример сервиса"""
from app.models.item import Item


class ExampleService:
    """Сервис для работы с элементами"""
    
    def __init__(self):
        # Временное хранилище (в реальном приложении используйте БД)
        self.items = {
            1: Item(1, 'Item 1', 'Description 1'),
            2: Item(2, 'Item 2', 'Description 2'),
        }
        self.counter = 2
    
    def get_all_items(self):
        """Получить все элементы"""
        return [item.to_dict() for item in self.items.values()]
    
    def get_item(self, item_id: int):
        """Получить элемент по ID"""
        item = self.items.get(item_id)
        return item.to_dict() if item else None
    
    def create_item(self, data: dict):
        """Создать новый элемент"""
        self.counter += 1
        item = Item(
            id=self.counter,
            name=data.get('name'),
            description=data.get('description')
        )
        self.items[item.id] = item
        return item.to_dict()
    
    def update_item(self, item_id: int, data: dict):
        """Обновить элемент"""
        if item_id not in self.items:
            return None
        
        item = self.items[item_id]
        item.name = data.get('name', item.name)
        item.description = data.get('description', item.description)
        return item.to_dict()
    
    def delete_item(self, item_id: int):
        """Удалить элемент"""
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False

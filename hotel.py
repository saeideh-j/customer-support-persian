
from langchain_core.language_models import BaseChatModel
from database import Database
from typing import List, Dict, Type, Optional
from datetime import datetime
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.callbacks.manager import CallbackManagerForToolRun
from utils import list_of_dict_to_str
from langchain_core.runnables import ensure_config

class HotelManager:
     
    def __init__(self, db: Database, llm: BaseChatModel) -> None:
        self.db = db
        self.llm = llm

    def get_tools(self) -> Dict[str, BaseTool]:
        tools = [
            SearchHotelsTool(hotel_manager=self),
            BookHotelsTool(hotel_manager=self),
            UpdateHotelsTool(hotel_manager=self),
            CancelHotelsTool(hotel_manager=self),
        ]
        return {tool.name: tool for tool in tools}
     
    def search_hotels(self,
        location: Optional[str] = None,
        name: Optional[str] = None,
        price_tier: Optional[str] = None,
        checkin_date: Optional[datetime] = None,
        checkout_date: Optional[datetime] = None,
    ) -> list[dict]:
        
        conn = self.db.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM hotels WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        # For the sake of this tutorial, we will let you match on any dates and price tier.
        cursor.execute(query, params)
        results = cursor.fetchall()

        conn.close()

        return [
            dict(zip([column[0] for column in cursor.description], row)) for row in results
        ]

    def book_hotel(self, hotel_id: int) -> str:
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully booked."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}."

    def update_hotel(self,
        hotel_id: int,
        checkin_date: Optional[datetime] = None,
        checkout_date: Optional[datetime] = None,
    ) -> str:
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if checkin_date:
            cursor.execute(
                "UPDATE hotels SET checkin_date = ? WHERE id = ?", (checkin_date, hotel_id)
            )
        if checkout_date:
            cursor.execute(
                "UPDATE hotels SET checkout_date = ? WHERE id = ?",
                (checkout_date, hotel_id),
            )

        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully updated."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}."

    def cancel_hotel(self, hotel_id: int) -> str:
      
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully cancelled."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}."

class CancelHotelsToolInput(BaseModel):
    pass

class CancelHotelsTool(BaseTool):
    name = 'cancel_hotels_tool'
    description = (
        "Cancel a hotel by its ID.\n"
        "Returns a message indicating whether the hotel was successfully cancelled or not."
    )
    args_schema: Type[BaseModel] = CancelHotelsToolInput # the tool expects a specific input schema
    return_direct: bool = False

    hotel_manager: HotelManager
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        
        config = ensure_config()
        configuration = config.get('configurable', {})
        hotel_id = configuration.get('hotel_id', None)
        
        if not hotel_id:
            raise ValueError("No `hotel_id` configured.")

        results = self.hotel_manager.cancel_hotel(
            hotel_id
        )
        return results

class UpdateHotelsToolInput(BaseModel):
    # hotel_id: int = Field(
    #     description="The ID of the hotel to update."
    # )

    checkin_date: Optional[str] = Field(
        description="must be empty or in iso format, specifies date or datetime which is the new check-in date of the hotel. Defaults to None."
    )
    checkout_date: Optional[str] = Field(
        description="must be empty or in iso format, specifies date or datetime which is the new check-out date of the hotel. this date should be at least one day after check_in date. Defaults to None."
    )
    # limit: Optional[int] = Field(description="specifies the maximum number of search results")

class UpdateHotelsTool(BaseTool):

    name = 'update_hotels_tool'
    description = (
        "Update a hotel's check-in and check-out dates by its ID.\n"
        "Returns a message indicating whether the hotel was successfully updated or not."
    )
    args_schema: Type[BaseModel] = UpdateHotelsToolInput # the tool expects a specific input schema
    return_direct: bool = False

    hotel_manager: HotelManager

    def _run(
        self,       
        checkin_date: Optional[datetime] = None,
        checkout_date: Optional[datetime] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        
        config = ensure_config()
        configuration = config.get('configurable', {})
        hotel_id = configuration.get('hotel_id', None)
        
        checkin_date = datetime.fromisoformat(checkin_date.replace('Z', '')) if checkin_date else None
        checkout_date = datetime.fromisoformat(checkout_date.replace('Z', '')) if checkout_date else None
        
        results = self.hotel_manager.update_hotel(
            hotel_id, checkin_date, checkout_date
        )
        return results


class SearchHotelsToolInput(BaseModel):

    location: (Optional[str]) = Field(
        description= "The location of the hotel. Defaults to None."
    )

    name: (Optional[str]) = Field(
        description="The name of the hotel. Defaults to None."
    )

    price_tier: (Optional[str]) = Field(
        description="The price tier of the hotel. Defaults to None. Examples: Midscale, Upper Midscale, Upscale, Luxury"
    )
     
    checkin_date: Optional[str] = Field(
        description="must be empty or in iso format, specifies date or datetime for search lower band"
    )
    checkout_date: Optional[str] = Field(
        description="must be empty or in iso format, specifies date or datetime for search upper band"
    )
    # limit: Optional[int] = Field(description="specifies the maximum number of search results")


class SearchHotelsTool(BaseTool):


    name = 'search_hotels_tool'
    description = (
        "Search for hotels based on location, name, price tier, check-in date, and check-out date.\n"
        "Returns A list of hotel dictionaries matching the search criteria."
    )
    args_schema: Type[BaseModel] = SearchHotelsToolInput # the tool expects a specific input schema
    return_direct: bool = False

    hotel_manager: HotelManager

    def _run(
        self,
        location: Optional[str] = None,
        name: Optional[str] = None,
        price_tier: Optional[str] = None,
        checkin_date: Optional[datetime] = None,
        checkout_date: Optional[datetime] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        location = location or None
        name = name or None
        price_tier = price_tier or None
        checkin_date = datetime.fromisoformat(checkin_date.replace('Z', '')) if checkin_date else None
        checkout_date = datetime.fromisoformat(checkout_date.replace('Z', '')) if checkout_date else None

        results = self.hotel_manager.search_hotels(
            location, name, price_tier, checkin_date, checkout_date
        )
        return list_of_dict_to_str(results)
    

class BookHotelsToolInput(BaseModel):
    pass
#    hotel_id: int = Field(description="should be the ID of the hotel to book.")
   


class BookHotelsTool(BaseTool):

    name = 'book_hotels_tool'
    description = (
        "Book a hotel by its ID.\n"
        "Returns a message indicating whether the hotel was successfully booked or not."
    )
    args_schema: Type[BaseModel] = BookHotelsToolInput # the tool expects a specific input schema
    return_direct: bool = False

    hotel_manager: HotelManager
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        
        config = ensure_config()
        configuration = config.get('configurable', {})
        hotel_id = configuration.get('hotel_id', None)
        
        # hotel_id = self.hotel_manager.get_hotel_id()
        # print("Current hotel_id:", hotel_id)
        if not hotel_id:
            raise ValueError("No `hotel_id` configured.")

        results = self.hotel_manager.book_hotel(
            hotel_id
        )
        return results
    


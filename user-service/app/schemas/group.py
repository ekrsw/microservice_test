from pydantic import BaseModel

class GroupBase(BaseModel):
    group_name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    pass
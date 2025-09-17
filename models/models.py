from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime


# Authentication Models

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None



# User

class User(BaseModel):
    id: Optional[int]
    name: str
    email: EmailStr
    password: str
    companyId: Optional[int]
    roleId: Optional[int]
    changePrompt: Optional[int]
    status: Optional[int]


# Company

class Company(BaseModel):
    id: Optional[int]
    companyName: str
    email: str
    apiKey: str
    companyLogo: str
    status: Optional[int]



# Role

class Role(BaseModel):
    id: Optional[int]
    roleName: str
    status: Optional[int]



# Role Prompt

class Role_Prompt(BaseModel):
    id: Optional[int]
    promptName: str
    promptDescription: str
    roleId: int
    companyId: int
    status: Optional[int]



# User Prompt

class User_Prompt(BaseModel):
    id: Optional[int]
    promptName: str
    promptDescription: str
    userId: int
    status: Optional[int]



# Job

class Job(BaseModel):
    id: Optional[int]
    jobName: str
    jobDescription: str
    companyId: int
    status: Optional[int]
    JdQuestions: Optional[str]
    jobId: Optional[int]
    clientName: Optional[str]
    clientIndustry: Optional[str]
    createdAt: Optional[datetime.datetime]
    updatedAt: Optional[datetime.datetime]



# Profile Match

class Profile_Match(BaseModel):
    id: Optional[int]
    jobId: int
    jobName: str
    userName: str
    email: str
    matchScore: int
    profile: str
    analysisReport: str
    analysisDate: str
    totalTokenUsed: Optional[int]
    totalCost: Optional[float]
    userId: int
    companyId: int
    analysisReportSkills: Optional[str]

"""
Job Interview Scenario Framework

This module provides a comprehensive framework for job interview simulations,
including various interview styles, position types, and a structured approach
to conducting realistic interview conversations.
"""

# Interview scenario template
JOB_INTERVIEW_SCENARIO = {
    "system_prompt": """You are an experienced job interviewer named {interviewer_name} for a {position_type} position.
Your role is to conduct a realistic job interview that helps the candidate practice their interview skills.

INTERVIEWER PROFILE:
- Name: {interviewer_name}
- Position: {interviewer_position}
- Company: {company_name}
- Interview Style: {interview_style}

INTERVIEW CONTEXT:
- Position being interviewed for: {position_title}
- Required skills: {required_skills}
- Experience level: {experience_level}
- Interview stage: {interview_stage}

INSTRUCTIONS:
- Maintain a professional demeanor appropriate for a real job interview
- Keep responses brief (2-3 sentences maximum) to maintain conversation flow
- Focus questions on assessing the candidate's fit for the {position_type} role
- Adapt your follow-up questions based on the candidate's previous responses
- If the candidate gives a vague answer, ask for specific examples
- Use natural language with occasional filler words for realism
- Do not break character or mention that you are an AI
- Transition naturally between different question types

CURRENT STAGE: {current_stage}

IMPORTANT DETAILS TO REMEMBER:
{context_memory}

As {interviewer_name}, conduct this interview professionally while providing a realistic experience for the candidate.
""",

    "stages": {
        "introduction": {
            "description": "Initial greeting and introduction",
            "interviewer_goals": [
                "Establish rapport with the candidate",
                "Briefly explain the interview process",
                "Make the candidate feel comfortable"
            ],
            "sample_questions": [
                "Welcome, thank you for joining us today. Could you start by telling me a bit about yourself?",
                "Good to meet you. Before we dive into specific questions, could you walk me through your background?",
                "Thanks for coming in today. To get started, I'd love to hear about your current role and responsibilities."
            ],
            "transition_cues": [
                "Thank you for that overview. Now I'd like to ask about your specific experiences.",
                "That's helpful context. Let's move on to talk about your relevant experience.",
                "Great introduction. I'd like to learn more about your skills related to this position."
            ]
        },
        
        "background_experience": {
            "description": "Questions about candidate's previous experience",
            "interviewer_goals": [
                "Assess relevance of past experience",
                "Identify transferable skills",
                "Understand career progression"
            ],
            "sample_questions": [
                "Could you describe a project you worked on that's relevant to this role?",
                "What aspects of your current position have prepared you for this opportunity?",
                "Tell me about a challenge you faced in your previous role and how you handled it."
            ],
            "transition_cues": [
                "Thank you for sharing that experience. Let's move on to some technical questions.",
                "That's useful context about your background. Now I'd like to assess some specific skills.",
                "I appreciate those insights. Let's switch gears to discuss some technical aspects of the role."
            ]
        },
        
        "technical_assessment": {
            "description": "Technical or skill-based questions",
            "interviewer_goals": [
                "Evaluate specific technical knowledge",
                "Assess problem-solving approach",
                "Determine skill proficiency level"
            ],
            "sample_questions": [
                "How would you approach {specific_technical_challenge}?",
                "Could you walk me through your process for {common_task_in_role}?",
                "What tools or methodologies do you use for {relevant_technical_area}?"
            ],
            "transition_cues": [
                "Thanks for explaining your technical approach. Let's discuss some behavioral scenarios.",
                "That gives me a good sense of your technical skills. Now I'd like to understand how you work with others.",
                "I appreciate your technical insights. Let's move to some questions about your work style and behaviors."
            ]
        },
        
        "behavioral_assessment": {
            "description": "Behavioral and situational questions",
            "interviewer_goals": [
                "Evaluate soft skills and interpersonal abilities",
                "Assess cultural fit",
                "Understand conflict resolution approach"
            ],
            "sample_questions": [
                "Tell me about a time when you had to resolve a conflict within your team.",
                "Describe a situation where you had to adapt quickly to changing requirements.",
                "Can you share an example of how you've handled criticism of your work?"
            ],
            "transition_cues": [
                "Thank you for sharing those examples. Let's discuss what you're looking for in your next role.",
                "Those are helpful insights into your working style. I'd like to know more about your career goals.",
                "I appreciate hearing about those experiences. Let's talk about what you're hoping to achieve in this position."
            ]
        },
        
        "candidate_questions": {
            "description": "Opportunity for candidate to ask questions",
            "interviewer_goals": [
                "Assess candidate's research and interest",
                "Provide genuine information about the role and company",
                "Evaluate candidate's priorities"
            ],
            "sample_questions": [
                "What questions do you have about the role or our company?",
                "Is there anything specific about the team or company culture you'd like to know?",
                "Do you have any questions about the next steps in our process?"
            ],
            "transition_cues": [
                "Those are good questions. As we wrap up, I'd like to share a bit more about next steps.",
                "Thank you for those questions. Let me briefly explain what happens after our interview today.",
                "I appreciate your thoughtful questions. Let me finish by outlining the rest of our hiring process."
            ]
        },
        
        "conclusion": {
            "description": "Wrapping up the interview",
            "interviewer_goals": [
                "Leave candidate with positive impression",
                "Clearly explain next steps",
                "Thank candidate for their time"
            ],
            "sample_questions": [],
            "sample_responses": [
                "Thank you for taking the time to speak with me today. We'll be in touch about next steps within {timeframe}.",
                "I've enjoyed our conversation today. Our team will review all candidates and follow up with you by {timeframe}.",
                "I appreciate you sharing your experience and insights today. We'll be making decisions about next steps by {timeframe}."
            ]
        }
    },
    
    "interviewer_styles": {
        "supportive": {
            "description": "A friendly, encouraging interviewer who makes candidates comfortable",
            "language_style": "Warm, affirming, uses positive reinforcement",
            "example_phrases": [
                "That's a great example.",
                "I really appreciate your thoughtful approach to that question.",
                "I can see how your experience would be valuable here."
            ]
        },
        
        "neutral": {
            "description": "A balanced, professional interviewer focused on fair assessment",
            "language_style": "Clear, direct, neither overly warm nor cold",
            "example_phrases": [
                "Thank you for that response.",
                "Let's move on to the next question.",
                "Could you elaborate on that point?"
            ]
        },
        
        "challenging": {
            "description": "An interviewer who tests candidates with difficult follow-ups",
            "language_style": "Probing, occasionally skeptical, pushes for depth",
            "example_phrases": [
                "That's interesting, but how would you handle [specific complication]?",
                "Can you provide evidence of the impact of your approach?",
                "What would you do differently if you encountered that situation again?"
            ]
        },
        
        "technical": {
            "description": "An interviewer focused on depth of technical knowledge",
            "language_style": "Precise, detail-oriented, uses field-specific terminology",
            "example_phrases": [
                "Could you explain the technical tradeoffs in your solution?",
                "What metrics did you use to evaluate success?",
                "Walk me through your implementation approach step by step."
            ]
        }
    },
    
    "position_types": {
        "software_engineer": {
            "required_skills": "Programming languages (e.g., Python, JavaScript), data structures, algorithms, system design",
            "technical_questions": [
                "How would you optimize a slow-performing database query?",
                "Explain how you would design a scalable API for our application.",
                "What strategies do you use for debugging complex issues?"
            ]
        },
        
        "product_manager": {
            "required_skills": "User research, stakeholder management, roadmap planning, data analysis",
            "technical_questions": [
                "How do you prioritize competing feature requests?",
                "Walk me through how you would validate a new product idea.",
                "How do you communicate technical constraints to non-technical stakeholders?"
            ]
        },
        
        "marketing_specialist": {
            "required_skills": "Campaign management, analytics, content creation, SEO/SEM",
            "technical_questions": [
                "How do you measure the success of a marketing campaign?",
                "What strategies would you use to increase our conversion rate?",
                "How do you stay current with changing marketing trends and technologies?"
            ]
        },
        
        "customer_service": {
            "required_skills": "Communication, problem-solving, empathy, conflict resolution",
            "technical_questions": [
                "How would you handle an angry customer who has been waiting for a resolution?",
                "What strategies do you use to ensure you understand a customer's needs?",
                "How do you balance quality of service with efficiency?"
            ]
        },
        
        "data_scientist": {
            "required_skills": "Statistical analysis, machine learning, data visualization, Python/R",
            "technical_questions": [
                "How would you approach a classification problem with imbalanced data?",
                "Explain the process you use for feature selection and engineering.",
                "How do you validate your models and ensure they don't overfit?"
            ]
        },
        
        "project_manager": {
            "required_skills": "Task management, risk assessment, team coordination, budgeting",
            "technical_questions": [
                "How do you handle a project that's falling behind schedule?",
                "What methodology do you use for tracking project progress?",
                "How do you manage stakeholder expectations when requirements change?"
            ]
        }
    },
    
    "feedback_parameters": {
        "communication_clarity": {
            "description": "Clarity and effectiveness of the candidate's communication",
            "assessment_criteria": [
                "Well-structured responses with clear beginning, middle, and end",
                "Appropriate use of technical terminology",
                "Concise answers that address the question directly"
            ]
        },
        
        "relevant_experience": {
            "description": "Relevance of examples provided to the position",
            "assessment_criteria": [
                "Examples demonstrate skills required for the role",
                "Quantifiable achievements and outcomes",
                "Appropriate detail level in describing experience"
            ]
        },
        
        "technical_proficiency": {
            "description": "Demonstrated technical knowledge and skills",
            "assessment_criteria": [
                "Accurate technical information",
                "Depth of understanding in key areas",
                "Awareness of best practices and methodologies"
            ]
        },
        
        "problem_solving": {
            "description": "Approach to solving problems and challenges",
            "assessment_criteria": [
                "Structured problem-solving methodology",
                "Consideration of multiple approaches",
                "Ability to handle unexpected aspects of problems"
            ]
        },
        
        "cultural_fit": {
            "description": "Alignment with company values and culture",
            "assessment_criteria": [
                "Values alignment with organization",
                "Collaboration and teamwork examples",
                "Adaptability to company environment"
            ]
        }
    },
    
    "company_profiles": {
        "tech_startup": {
            "description": "A fast-growing technology startup with an innovative product",
            "values": ["Innovation", "Agility", "Growth mindset", "Collaboration"],
            "work_environment": "Fast-paced, flexible, casual culture with flat hierarchy"
        },
        
        "enterprise_corporation": {
            "description": "An established enterprise company with structured processes",
            "values": ["Reliability", "Professionalism", "Excellence", "Integrity"],
            "work_environment": "Structured, process-oriented with clear career paths"
        },
        
        "creative_agency": {
            "description": "A creative agency focused on design and marketing",
            "values": ["Creativity", "Client focus", "Quality", "Originality"],
            "work_environment": "Collaborative, project-based work with creative freedom"
        },
        
        "nonprofit_organization": {
            "description": "A nonprofit organization with a mission-driven focus",
            "values": ["Mission impact", "Community", "Empathy", "Sustainability"],
            "work_environment": "Purpose-driven, community-oriented, resourceful"
        }
    },
    
    "experience_levels": {
        "entry_level": {
            "description": "0-2 years of experience, suitable for recent graduates",
            "question_focus": "Education, internships, projects, learning ability",
            "expectations": "Basic understanding of role fundamentals, eagerness to learn"
        },
        
        "mid_level": {
            "description": "3-5 years of experience, demonstrated professional success",
            "question_focus": "Practical experience, specific achievements, technical depth",
            "expectations": "Strong technical skills, independence, some leadership"
        },
        
        "senior_level": {
            "description": "6+ years of experience, deep expertise and leadership",
            "question_focus": "Strategic thinking, leadership, complex problem solving",
            "expectations": "Expert knowledge, mentorship ability, organizational impact"
        }
    },
    
    "interviewer_names": {
        "neutral": ["Alex Johnson", "Morgan Zhang", "Jordan Rivera", "Taylor Wilson"],
        "supportive": ["Sam Brooks", "Jamie Chen", "Casey Thompson", "Riley Garcia"],
        "challenging": ["Dr. Morgan Reed", "Victoria Palmer", "Michael Sterling", "Alexis Wright"],
        "technical": ["Dr. Ray Chen", "Priya Patel", "Eliot Washington", "Cameron Martinez"]
    }
}


def get_interview_prompt(
    position_type="software_engineer",
    interview_style="neutral",
    experience_level="mid_level",
    company_type="tech_startup",
    stage="introduction",
    context_memory=""
):
    """
    Generate a formatted interview prompt based on specified parameters.
    
    Args:
        position_type: Type of position (e.g., software_engineer, product_manager)
        interview_style: Style of interviewer (e.g., supportive, challenging)
        experience_level: Level of experience expected (e.g., entry_level, senior_level)
        company_type: Type of company (e.g., tech_startup, enterprise_corporation)
        stage: Current interview stage (e.g., introduction, technical_assessment)
        context_memory: String containing important context from previous exchanges
        
    Returns:
        Formatted system prompt for the interview scenario
    """
    scenario = JOB_INTERVIEW_SCENARIO
    
    # Select position details
    position_info = scenario["position_types"].get(
        position_type, 
        scenario["position_types"]["software_engineer"]
    )
    
    # Select experience level
    exp_info = scenario["experience_levels"].get(
        experience_level,
        scenario["experience_levels"]["mid_level"]
    )
    
    # Select company profile
    company_info = scenario["company_profiles"].get(
        company_type,
        scenario["company_profiles"]["tech_startup"]
    )
    
    # Select interviewer style
    style_info = scenario["interviewer_styles"].get(
        interview_style,
        scenario["interviewer_styles"]["neutral"]
    )
    
    # Select a name based on interviewer style
    import random
    interviewer_name = random.choice(
        scenario["interviewer_names"].get(
            interview_style, 
            scenario["interviewer_names"]["neutral"]
        )
    )
    
    # Determine position title
    position_title = position_type.replace("_", " ").title()
    
    # Format the prompt with all selected information
    formatted_prompt = scenario["system_prompt"].format(
        interviewer_name=interviewer_name,
        interviewer_position=f"Senior {position_title}",
        company_name=f"{company_info['description'].split()[0].title()} {company_type.split('_')[0].title()}",
        position_type=position_type.replace("_", " "),
        position_title=position_title,
        required_skills=position_info["required_skills"],
        experience_level=exp_info["description"],
        interview_stage=exp_info["question_focus"],
        interview_style=style_info["description"],
        current_stage=stage,
        context_memory=context_memory or "No previous context yet."
    )
    
    return formatted_prompt


def get_stage_questions(position_type, stage):
    """
    Get sample questions for a specific interview stage and position type.
    
    Args:
        position_type: Type of position (e.g., software_engineer)
        stage: Interview stage (e.g., technical_assessment)
        
    Returns:
        List of sample questions
    """
    scenario = JOB_INTERVIEW_SCENARIO
    
    # Get stage information
    stage_info = scenario["stages"].get(
        stage,
        scenario["stages"]["introduction"]
    )
    
    # Get base questions from the stage
    questions = stage_info.get("sample_questions", [])
    
    # For technical stage, add position-specific questions
    if stage == "technical_assessment":
        position_info = scenario["position_types"].get(
            position_type,
            scenario["position_types"]["software_engineer"]
        )
        questions.extend(position_info.get("technical_questions", []))
    
    return questions


def generate_interview_context(previous_exchanges, max_tokens=1000):
    """
    Generate a concise context memory from previous exchanges.
    
    Args:
        previous_exchanges: List of dictionaries with 'role' and 'content' keys
        max_tokens: Maximum approximate token count for context
        
    Returns:
        Formatted context string for the prompt
    """
    if not previous_exchanges:
        return "No previous context yet."
    
    # Extract key information
    key_points = []
    
    # Always include the first exchange (introduction)
    if len(previous_exchanges) >= 2:
        candidate_intro = previous_exchanges[1].get("content", "") if previous_exchanges[1].get("role") == "user" else ""
        if candidate_intro:
            key_points.append(f"Candidate introduction: {candidate_intro[:100]}...")
    
    # Track mentioned skills, experiences, and qualities
    mentioned_skills = set()
    mentioned_experience = []
    
    # Process exchanges to extract key information
    for exchange in previous_exchanges:
        if exchange.get("role") == "user":
            content = exchange.get("content", "").lower()
            
            # Extract mentioned skills (simple keyword extraction)
            skill_keywords = ["python", "javascript", "java", "react", "angular", "node", "aws", 
                              "cloud", "database", "sql", "nosql", "agile", "scrum", "leadership",
                              "management", "communication", "team", "project", "analysis"]
            
            for skill in skill_keywords:
                if skill in content and skill not in mentioned_skills:
                    mentioned_skills.add(skill)
            
            # Look for experience mentions (simple heuristic)
            experience_phrases = ["worked on", "developed", "created", "managed", "led", "team of", "years of"]
            for phrase in experience_phrases:
                if phrase in content:
                    # Extract the sentence containing the phrase
                    sentence_start = max(0, content.find(phrase) - 30)
                    sentence_end = min(len(content), content.find(phrase) + 70)
                    experience = content[sentence_start:sentence_end].strip()
                    mentioned_experience.append(experience)
    
    # Format the context
    if mentioned_skills:
        key_points.append(f"Mentioned skills: {', '.join(mentioned_skills)}")
    
    if mentioned_experience:
        # Limit to 3 most recent experiences
        for i, exp in enumerate(mentioned_experience[-3:]):
            key_points.append(f"Experience {i+1}: {exp}")
    
    # Add any specific achievements or challenges mentioned
    # This would require more sophisticated NLP in a real implementation
    
    # Combine all key points
    context = "\n".join(key_points)
    
    # Ensure it's not too long (rough approximation of tokens)
    if len(context) > max_tokens * 4:  # ~4 chars per token
        context = context[:max_tokens * 4] + "..."
    
    return context

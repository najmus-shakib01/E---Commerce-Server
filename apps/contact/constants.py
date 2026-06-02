class InquirySubject:
    GENERAL_INQUIRY     = "GENERAL_INQUIRY"
    ORDER_ISSUE         = "ORDER_ISSUE"
    PRODUCT_FEEDBACK    = "PRODUCT_FEEDBACK"
    TECHNICAL_SUPPORT   = "TECHNICAL_SUPPORT"

    CHOICES = [
        (GENERAL_INQUIRY,   "General Inquiry"),
        (ORDER_ISSUE,       "Order Issue"),
        (PRODUCT_FEEDBACK,  "Product Feedback"),
        (TECHNICAL_SUPPORT, "Technical Support"),
    ]

    BANGLA_LABELS = {
        GENERAL_INQUIRY:   "সাধারণ জিজ্ঞাসা",
        ORDER_ISSUE:       "অর্ডার সমস্যা",
        PRODUCT_FEEDBACK:  "পণ্যের মতামত",
        TECHNICAL_SUPPORT: "প্রযুক্তিগত সহায়তা",
    }

    BADGE_COLORS = {
        GENERAL_INQUIRY:   "#3b82f6",   
        ORDER_ISSUE:       "#ef4444",  
        PRODUCT_FEEDBACK:  "#8b5cf6",  
        TECHNICAL_SUPPORT: "#f59e0b",   
    }
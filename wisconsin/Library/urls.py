from django.urls import path, include
from .views import librarybase
from . import views 
from . views import *
from .views import research_support, instruction_support, about, librarybase,people, help
# Navina

urlpatterns = [

    # ***** library_admin *****
    path("", include("Library.library_admin.urls")),

    path('', views.libraryhome, name='library_home'),

    path('find/', views.library_find, name='library_find'),

    path('borrow_req/', views.library_borrow_req, name='library_borrow_req'),

    path('locations/', views.library_locations, name='library_locations'),

    path('give/', views.library_give, name='library_give'),

    path('search/', views.search_base, name='search_base'),

    path("catalog-search/", views.catalog_search, name="catalog_search"),

    path("citation-search/",views.citation_search,name="citation_search"),

    path("advanced-search/",views.advanced_search,name="advanced_search",),

    path("browse-subjects/",views.browse_subjects,name="browse_subjects",),

    path("access/",views.library_access,name="library_access"),

    path("catalog/book/<int:pk>/",views.book_details,name="book_details",),

    path( "browse-by-format/", views.browse_by_format, name="browse_by_format"),

    path("introductory-databases/",views.introductory_databases,name="introductory_databases"),

    path("explore-by-subject/",views.explore_by_subject,name="explore_by_subject",),

    path("popular/",views.popular_databases,name="popular_databases",),

    path("journals/browse-title/",views.journal_browse_by_title,name="journal_browse_by_title",),

    path("databases/",views.databases,name="databases",),

    path("articles/", views.articles, name="articles",),

    path("catalog/browse/",views.catalog_browse,name="catalog_browse",),

    path("find/ebooks/",views.ebooks,name="ebooks",),

    path("find/dissertations/", views.dissertations, name="dissertations",),

    path("find/dissertations/other-university/",views.other_university_dissertations,name="other_university_dissertations",),

    path("find/dissertations/prepare-deposit/",views.prepare_deposit,name="prepare_deposit",),
    
    path("find/browzine/", views.browzine, name="browzine",),
    
    path("journals/browse/",views.journals_browse,name="journals_browse",),

    path("borrow-request/borrowing-policies/",views.borrowing_policies,name="borrowing_policies",),

    path("borrow-request/renew-materials/",views.renew_materials,name="renew_materials",),

    path("borrow-request/return-materials/",views.return_materials,name="return_materials",),

    path("borrow-request/open-return-libraries/",views.open_return_libraries,name="open_return_libraries",),

    path("borrow-request/outside-book-returns/",views.outside_book_returns,name="outside_book_returns",),

    path("borrow-request/borrowing-history/",views.borrowing_history,name="borrowing_history",),

    path("borrow-request/fines-blocks-holds/",views.fines_blocks_holds,name="fines_blocks_holds",),

    path("borrow-request/lost-or-damaged-items/",views.lost_or_damaged_items,name="lost_or_damaged_items",),

    path("borrow-request/appeal-library-charges/",views.appeal_library_charges,name="appeal_library_charges",),

    path("borrow-request/request-dissertation-thesis/",views.request_dissertation_thesis,name="request_dissertation_thesis",),

    path("borrow-request/request-articles/",views.request_articles,name="request_articles",),

    path("borrow-request/request-materials/",views.request_materials,name="request_materials",),
    
    path("borrow-request/not-affiliated/",views.not_affiliated_uw,name="not_affiliated_uw",),

    path("borrow-request/shelving-facilities/",views.shelving_facilities,name="shelving_facilities",),

    path("borrow-request/on-campus-shelving-facilities/",views.on_campus_shelving_facilities,name="on_campus_shelving_facilities",),

    path("borrow-request/request-materials-shelving-facilities/",views.request_materials_shelving_facilities,name="request_materials_shelving_facilities",),
    
    path("borrow-request/shelving-facility-faq/",views.shelving_facility_faq,name="shelving_facility_faq",),
    
    path("borrow-request/libraries-collections-preservation-facility/",views.libraries_collections_preservation_facility,name="libraries_collections_preservation_facility",),

    path("preservation-facility-faq/",views.preservation_facility_faq,name="preservation_facility_faq",),

    path("project-organization/",views.project_organization,name="project_organization",),

    path("verona-shelving-facility/",views.verona_shelving_facility,name="verona_shelving_facility",),

    path("request-book-chapters/",views.request_book_chapters,name="request_book_chapters",),

    path("request-books-media/",views.request_books_media,name="request_books_media",),

    path("interlibrary-loan/",views.interlibrary_loan,name="interlibrary_loan",),

    path("borrow/interlibrary-loan/copyright/",views.interlibrary_loan_copyright,name="interlibrary_loan_copyright",),

    path("contact-us/",views.contact_us,name="contact_us",),

    path("borrow/pickup-by-appointment/",views.pickup_by_appointment,name="pickup_by_appointment",),

    path("borrow/request-purchase/",views.request_purchase,name="request_purchase",),

    path("borrow/shelving-request/",views.shelving_request,name="shelving_request",),

    path("borrow/other-libraries/",views.other_libraries,name="other_libraries",),

    path("borrow/uw-madison-alumni/",views.uw_madison_alumni,name="uw_madison_alumni",),

    path("borrow-request/ill-lending/",views.ill_lending,name="ill_lending",),

    path("borrow-request/contact-us/",views.ill_contact_us,name="ill_contact_us",),

    path("library/borrow/policies-and-charges/",views.policies_and_charges,name="policies_and_charges",),

    path("library/borrow/billing-and-shipping/",views.billing_and_shipping,name="billing_and_shipping",),

    path("library/borrow/credit-card-payments/",views.credit_card_payments,name="credit_card_payments",),

    path("library/media-for-courses/",views.media_for_courses,name="media_for_courses",),

    path("library/students-accessing-course-materials/",views.students_accessing_course_materials,name="students_accessing_course_materials",),

    path("library/textbooks-initiative/",views.textbooks_initiative,name="textbooks_initiative",),

    path("library/streaming-video-database-information/",views.streaming_video_database_information,name="streaming_video_database_information",),

    path("account/",views.library_account,name="library_account"),

    # rupa code
    path('librarybase/', librarybase, name='library_base'),
    path(
        'research-support/',
        research_support,
        name='research_support'
    ),

    # path(
    #     "research-support/data-management-plan/",
    #     views.data_management_plan_detail,
    #     name="data_management_plan_detail",
    # ),
    # path(
    #     "research-support/grants-scholarships/<slug:slug>/",
    #     views.grants_scholarships_detail,
    #     name="grants_scholarships_detail",
    # ),
    # path(
    # "research-support/evidence-synthesis/<slug:slug>/",
    # views.evidence_synthesis_detail,
    # name="evidence_synthesis_detail",
    # ),

    # path(
    # "research-support/<slug:slug>/",
    # views.research_support_detail,
    # name="research_support_detail",
    # ),
    path(
        'instruction-support/',
        instruction_support,
        name='instruction_support'
    ),
    path(
        "instruction-request/",
        views.instruction_request,
        name="instruction_request",
    ),
    path(
        'lib-about/',
        about,
        name='lib_about'
    ),
    path(
        "lib-about/collections/",
        views.collections,
        name="collections",
    ),

    path(
        "lib-about/dataset-acquisition-policy/",
        views.dataset_acquisition_policy,
        name="dataset_acquisition_policy"
    ),

    path(
        "lib-about/managing-physical-collections/",
        views.managing_physical_collections,
        name="managing_physical_collections"
    ),

    path(
        "lib-about/campus-collections-plan/",
        views.campus_collections_plan,
        name="campus_collections_plan"
    ),
    path(
        "lib-about/print-journal-management/",
        views.print_journal_management,
        name="print_journal_management"
    ),

    path(
        "lib-about/shared-print-projects/",
        views.shared_print_projects,
        name="shared_print_projects",
    ),

    path(
        "lib-about/collections/preservation/",
        views.preservation,
        name="preservation",
    ),

    path(
        "research-support/scholarly-communication/",
        views.scholarly_communication,
        name="scholarly_communication",
    ),


    path("people/", people, name="people"),

    path(
    "people/directory/",
    views.people_directory,
    name="people_directory",
    ),

    path(
        "people/profile/<int:staff_id>/",
        views.staff_profile,
        name="staff_profile",
    ),

    

    path('help/', help, name="help"),

    # path(
    #     "help/topic/<slug:slug>/",
    #     views.help_topic_detail,
    #     name="help_topic_detail",
    # ),
     path(
        "people/office-of-the-dean/",
        views.office_of_the_dean,
        name="office_of_the_dean",
    ),
    path(
    "people/subject-librarians/",
    views.subject_librarians,
    name="subject_librarians",
    ),

    path(
        "planning-your-research-project/",
        views.planning_research_project,
        name="planning_research_project",
    ),
    path(
        "evidence-synthesis-systematic-reviews/",
        views.evidence_synthesis,
        name="evidence_synthesis",
    ),

    path('circulation-assistance/', views.circulation_assistance, name='circulation_assistance'),

    path(
        "id-problems/",
        views.id_problems,
        name="id_problems",
    ),
    path(
        "off-campus-access/",
        views.off_campus_access,
        name="off_campus_access",
    ),
    path(
        "library-catalog-help/",
        views.library_catalog_help,
        name="library_catalog_help",
    ),
    path(
        "research-support-cards/",
        views.research_support_cards,
        name="research_support_cards",
    ),

    path(
        "technical-assistance/",
        views.technical_assistance,
        name="technical_assistance",
    ),

    path(
        "research-support/finding-evaluating-information/",
        views.finding_evaluating_information,
        name="finding_evaluating_information",
    ),

    path(
        "research-support/data-services/",
        views.data_services,
        name="data_services",
    ),

    # path(
    #     "research-support/reusing-data/",
    #     views.reusing_data,
    #     name="reusing_data",
    # ),

    path(
    "borrow-request/interlibrary-loan/interlibrary-loan-faq/",
    views.interlibrary_loan_faq,
    name="interlibrary_loan_faq",
    ),
# index data
    path(
        "research-support/finding-reusing-citing-data/",
        views.finding_reusing_citing_data,
        name="finding_reusing_citing_data",
    ),

      path(
        "research-support/collecting-organizing-analyzing-information/",
        views.collecting_organizing_analyzing_information,
        name="collecting_organizing_analyzing_information",
    ),
    path(
        "research-support/patent-services/",
        views.patent_services,
        name="patent_services",
    ),

    path(
        "research-support/citation-managers/",
        views.citation_managers,
        name="citation_managers",
    ),

    path(
        "instruction-support/library-instruction-options/",
        views.library_instruction_options,
        name="library_instruction_options",
    ),
    path(
        "collections/grants-information-collection/",
        views.grants_information_collection,
        name="grants_information_collection",
    ),
     path(
        "consultants/",
        views.consultants,
        name="consultants",
    ),

    path(
        "electronic-laboratory-notebooks/",
        views.electronic_lab_notebooks,
        name="electronic_lab_notebooks",
    ),
    path(
        "research-support/publishing-sharing-your-research/",
        views.publishing_sharing_research,
        name="publishing_sharing_research",
    ),
    path(
        "research-support/scholarly-communication/copyright-resources/",
        views.copyright_resources,
        name="copyright_resources",
    ),
    path(
        "research-support/scholarly-communication/copyright-resources/how-to-use-others-materials/",
        views.how_to_use_others_materials,
        name="how_to_use_others_materials",
    ),
    path(
        "research-support/scholarly-communication/copyright-resources/managing-your-copyright/",
        views.managing_your_copyright,
        name="managing_your_copyright",
    ),

    path(
        "research-support/scholarly-communication/copyright-resources/navigating-copyright-in-moving-courses-online/",
        views.navigating_copyright_online,
        name="navigating_copyright_online",
    ),

    path(
        "research-support/scholarly-communication/copyright-resources/copyright-basics/",
        views.copyright_basics,
        name="copyright_basics",
    ),
    path(
        "research_support/measuring-impact/",
        views.measuring_impact,
        name="measuring_impact"
    ),
    path(
        "research-support/curating-preserving-research-outputs/",
        views.curating_research_outputs,
        name="curating_research_outputs",
    ),

    path(
        "research-support/digital-collections/submitting-project-proposal/",
        views.submitting_digital_collections_proposal,
        name="submitting_digital_collections_proposal",
    ),
    path(
        "research-support/literature-review/",
        views.literature_review,
        name="literature_review",
    ),
    path(
        "research-support/consultations/",
        views.consultations,
        name="consultations",
    ),

    path(
        "research-support/public-access/",
        views.public_access,
        name="public_access",
    ),
    path(
    "research-support/library-support-open-access/",
    views.library_support_open_access,
    name="library_support_open_access",
    ),
    path(
    "research-support/open-access/",
    views.open_access,
    name="open_access",
    ),

    path(
        "research-support/ensuring-scientific-rigor/",
        views.ensuring_scientific_rigor,
        name="ensuring_scientific_rigor",
    ),

    path(
        "research-support/scholarly-communication/open-access/public-access/funder-public-access-requirements/",
        views.funder_public_access_requirements,
        name="funder_public_access_requirements",
    ),

    path(
        "open-access/public-access/core-resource-acknowledgements/",
        views.core_resource_acknowledgements,
        name="core_resource_acknowledgements",
    ),

    path(
    "research-support/digital-collections/submitting-project-proposal/form/",
    views.proposal_submission_form,
    name="proposal_submission_form",
    ),
    path(
        "research-support/digital-collections/contact/",
        views.contact_digital_collections,
        name="contact_digital_collections",
    ),

     path(
        "instruction-support/library-services-canvas/",
        views.library_services_canvas,
        name="library_services_canvas",
    ),
    path(
        "instruction-support/course-content-support/",
        views.course_content_support,
        name="course_content_support",
    ),
     path(
        "instruction-support/research-guides/",
        views.research_guides,
        name="research_guides",
    ),
      path(
        "instruction-support/designing-assignments/",
        views.designing_assignments,
        name="designing_assignments",
    ),

    path(
        "instruction-support/spaces-to-support-instruction/",
        views.spaces_to_support_instruction,
        name="spaces_to_support_instruction",
    ),

    path(
    "instruction-support/undergraduate-services/",
    views.undergraduate_services,
    name="undergraduate_services",
    ),
    path(
        "instruction-support/resources-to-support-instructors/",
        views.resources_to_support_instructors,
        name="resources_to_support_instructors",
    ),
    path(
    "instruction-support/sift-winnow/",
    views.sift_winnow,
    name="sift_winnow",
    ),
    path(
    "instruction-support/avoiding-plagiarism/",
    views.avoiding_plagiarism,
    name="avoiding_plagiarism",
    ),
    path(
        "borrow-request/remote-delivery/",
        views.remote_delivery,
        name="remote_delivery",
    ),
    path(
    "about/diversity/",
    views.diversity_equity_inclusion,
    name="diversity_equity_inclusion",
    ),
    path(
        "about/",
        views.about_page,
        name="about_page"
    ),
    path(
        "about/employment/",
        views.employment,
        name="employment",
    ),
    path(
        "about/featured-news-resources/",
        views.featured_news_resources,
        name="featured_news_resources",
    ),
     path(
        "about/jobs/",
        views.jobs_home,
        name="jobs_home",
    ),
    path(
        "about/contact/",
        views.contact,
        name="contact",
    ),
    path(
        "about/diversity-strategic-plan/",
        views.diversity_strategic_plan,
        name="diversity_strategic_plan",
    ),
    
    path(
        "about/diversity-inclusion/",
        views.diversity_inclusion,
        name="diversity_inclusion",
    ),
    path(
        "about/employment-card/",
        views.employment_card,
        name="employment_card",
    ),
    path(
        "instruction-support/content-resources/",
        views.instruction_support_content_resources,
        name="instruction_support_content_resources",
    ),
    path(
        "instruction-support/library-research-tutorials/",
        views.library_research_tutorials,
        name="library_research_tutorials",
    ),
    path(
        "teaching-learning/micro-courses/",
        views.micro_courses,
        name="micro_courses",
    ),
    
    path(
        "research-support/data-management-plan/",
        views.data_introduction,
        name="introduction",
    ),
    
    path(
        "research-support/data-management-plan/why-create/",
        views.dmp_why_create_plan,
        name="dmp_why_create_plan",
    ),
    
    path(
        "research-support/data-management-plan/use-dmptool/",
        views.dmp_use_dmptool,
        name="dmp_use_dmptool",
    ),
    
    path(
        "research-support/data-management-plan/data-type/",
        views.dmp_data_type,
        name="dmp_data_type",
    ),
    path(
        "research-support/data-management-plan/related-tools/",
        views.dmp_related_tools,
        name="dmp_related_tools",
    ),
    
    path(
        "research-support/data-management-plan/standards/",
        views.dmp_standards,
        name="dmp_standards",
    ),
    path(
        "research-support/data-management-plan/data-preservation/",
        views.dmp_data_preservation,
        name="dmp_data_preservation",
    ),
    path(
        "research-support/data-management-plan/data-sharing/",
        views.dmp_data_sharing,
        name="dmp_data_sharing",
    ),
    
    path(
        "research-support/data-management-plan/oversight/",
        views.dmp_oversight,
        name="dmp_oversight",
    ),
    path(
        "research-support/grants-scholarships-static/",
        views.grants_scholarships_static,
        name="grants_scholarships_static",
    ),
    
    path(
        "research-support/grants/building-nonprofit-board/",
        views.building_nonprofit_board,
        name="building_nonprofit_board",
    ),
    path(
        "research-support/grants/finding-federal-funding/",
        views.finding_federal_funding,
        name="finding_federal_funding",
    ),
    path(
        "research-support/grants/funding-academics-researchers/",
        views.funding_academics_researchers,
        name="funding_academics_researchers",
    ),
    
    path(
        "research-support/grants/funding-graduate-students/",
        views.funding_graduate_students,
        name="funding_graduate_students",
    ),
    path(
        "research-support/grants/funding-individuals/",
        views.funding_individuals,
        name="funding_individuals",
    ),
    path(
        "research-support/grants/funding-international-students/",
        views.funding_international_students,
        name="funding_international_students",
    ),
    path(
        "research-support/grants/study-abroad/",
        views.funding_study_abroad,
        name="funding_study_abroad",
    ),
    path(
        "research-support/grants/undergraduates/",
        views.funding_undergraduates,
        name="funding_undergraduates",
    ),
    path(
        "research-support/funding-students/",
        views.funding_students,
        name="funding_students",
    ),
    path(
        "research-support/grant-funding-individuals/",
        views.grant_funding_individuals,
        name="grant_funding_individuals",
    ),
    path(
        "research-support/funding-nonprofit/",
        views.grant_funding_nonprofit,
        name="grant_funding_nonprofit",
    ),
    path(
        "research-support/proposal-writing/",
        views.proposal_writing,
        name="proposal_writing"
    ),
    path(
        "research-support/nonprofit-startup/",
        views.nonprofit_startup,
        name="nonprofit_startup",
    ),
    path(
        "research-support/prospect/",
        views.prospect,
        name="prospect",
    ),
    path(
        "research-support/corporate-giving/",
        views.corporate_giving,
        name="corporate_giving",
    ),
    path(
        "research-support/grants-for-nonprofits/",
        views.grants_for_nonprofits,
        name="grants_for_nonprofits",
    ),
    path(
        "research-support/wisconsin/",
        views.wisconsin,
        name="wisconsin",
    ),
    path(
        "research-support/minds/",
        views.minds,
        name="minds",
    ),

]

# rupa code


